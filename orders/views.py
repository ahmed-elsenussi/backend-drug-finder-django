
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.conf import settings
import stripe
from rest_framework.decorators import action
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from geopy.distance import geodesic  # [OKS] For distance calculation
from .models import Order
from payments.models import Payment
from .serializers import OrderSerializer
from .permissions import OrderAccessPermission
from inventory.permissions import IsAdminCRU
from inventory.models import Medicine
from notifications.utils import send_notification 
from .filters import OrderFilter
from rest_framework.pagination import PageNumberPagination
import decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

# [SARA]: Custom pagination class for orders (limit 10)
class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# [SARA]: Filtering enabled for OrderViewSet (store, order_status, client)
class OrderViewSet(viewsets.ModelViewSet):
    # [SARA]: Use OrderSerializer for all order operations
    serializer_class = OrderSerializer
    # [SARA]: Admins (IsAdminCRU) can CRU, others use OrderAccessPermission
    permission_classes = [IsAuthenticated, IsAdminCRU | OrderAccessPermission]
    filter_backends = [DjangoFilterBackend]  # [SARA]
    filterset_class = OrderFilter  # [SARA]
    pagination_class = OrderPagination  # [SARA]

    # [SARA]: Custom queryset based on user role
    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.none() 
       
        # [OK - SARA] filtering with authorization 
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            queryset = Order.objects.all().order_by('-timestamp')
        elif user.role == 'pharmacist':
            queryset = Order.objects.filter(store__owner__user=user).order_by('-timestamp')
        elif user.role == 'client':
            queryset = Order.objects.filter(client__user=user).order_by('-timestamp')
            
        return queryset

    # [OKS] change name to create
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        payment_method = data.get("payment_method", "cash")
        store_id = data.get("store")
        
        #[OKS] add transaction [multiple steps that must be treated as one unit of work] 
        with transaction.atomic(): #[OKS] block happen atomically
            try:
                self._validate_medicine_quantities(data.get('items', []))
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            # [SARA]: Allow admin to create order for any user, client for self only
            if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
                order = serializer.save()
                cart_user = user
            elif user.role == 'client':
                client = getattr(user, 'client', None)
                if not client:
                    raise PermissionError('No client profile found for this user.')
                # [OKS] Save client and store in the order
                save_kwargs = {'client': client}
                if store_id:
                    save_kwargs['store_id'] = store_id
                    
                order = serializer.save(**save_kwargs)
                cart_user = client.user
            else:
                raise PermissionError('Only clients and admins can create orders.')
            
            # [OKS] Calculate shipping cost before updating totals
            shipping_cost = self._calculate_shipping_cost(order)
            # [OKS] Calculate tax based on subtotal (before shipping)
            tax = self._calculate_tax(order.total_price)
            
            # [OKS] Update order with shipping and tax
            order.shipping_cost = shipping_cost
            order.tax = tax
            order.total_with_fees = order.total_price + shipping_cost + tax    
            order.save()
            
            # [OKS] Update medicine quantities
            self._update_medicine_quantities(order.items)
            
            #[OKS] notify the pharmacist
            if order.store and order.store.owner:
                pharmacist_user = order.store.owner.user
                send_notification(
                    user=pharmacist_user,
                    message=f"You have a new order #{order.id} from {order.client.user.name}",
                    notification_type='message',
                    data={
                        'order_id': order.id,
                        'client_name': order.client.user.name,
                        'total_amount': str(order.total_price),
                        'shipping_cost': str(shipping_cost),
                        'tax': str(tax)
                    }
                )

         

            # [OKS] Create Payment record (include total with shipping and tax)
            total_with_fees = order.total_with_fees
            Payment.objects.create(
                order=order,
                client=order.client,
                amount=total_with_fees,
                payment_method=payment_method,
                status='pending' if payment_method == 'cash' else 'initiated'
            )

            response_data = {
                'order': OrderSerializer(order).data,
                'shipping_cost': shipping_cost,
                'tax': tax,
                'total_with_fees': total_with_fees
            }

            # [OKS] Handle Stripe if needed
            if payment_method == 'cash':
                order.order_status = 'pending'
                order.save()
            elif payment_method == 'card':
                try:
                    # [OKS] Include shipping and tax in Stripe payment
                    intent = stripe.PaymentIntent.create(
                        amount=int(float(total_with_fees) * 100),  # Convert to cents
                        currency='usd',
                        metadata={
                            'order_id': order.id,
                            'shipping_cost': str(shipping_cost),
                            'tax': str(tax)
                        },
                        payment_method_types=['card'],
                        capture_method='automatic'
                    )
                    response_data['client_secret'] = intent.client_secret
            
                    #[OKS] Check if payment was immediately successful
                    if intent.status == 'succeeded':
                        order.order_status = 'paid'
                        order.save()
                        send_notification(
                            user=order.client.user,
                            message=f"Payment successful for order #{order.id}",
                            notification_type='system',
                            data={
                                'order_id': order.id,
                                'total_paid': str(total_with_fees)
                            }
                        )
                except Exception as e:
                    raise ValidationError(f"Stripe error: {str(e)}")
            else:
                raise ValidationError('Invalid payment method.')

            return Response(response_data, status=status.HTTP_201_CREATED)
    
    # [OKS] Calculate shipping cost based on distance
    def _calculate_shipping_cost(self, order):
        if not order.store or not order.client:
            return decimal.Decimal('0')  
        
        store_location = (order.store.latitude, order.store.longitude)
        client_location = (order.client.default_latitude, order.client.default_longitude)
        
        try:
            distance_km = geodesic(store_location, client_location).kilometers
        except:
            return decimal.Decimal(str(settings.DEFAULT_SHIPPING_COST))
        
        if distance_km <= 5:
            return decimal.Decimal('5.00')
        elif distance_km <= 20:
            return decimal.Decimal('10.00')
        elif distance_km <= 50:
            return decimal.Decimal('15.00')
        else:
            return decimal.Decimal('25.00')

    def _calculate_tax(self, subtotal):
        tax_rate = decimal.Decimal(str(getattr(settings, 'SALES_TAX_RATE', 0.08)))
        return (subtotal * tax_rate).quantize(decimal.Decimal('0.00'))

    # [OKS] Validate medicine quantities before order creation
    def _validate_medicine_quantities(self, items):
        if not items:
            raise ValidationError("Order must contain at least one item")
            
        for item in items:
            try:
                medicine_id = item.get('item_id')
                quantity = item.get('ordered_quantity')
                
                if not medicine_id or not quantity:
                    raise ValidationError("Each item must have item_id and ordered_quantity")
                
                medicine = Medicine.objects.get(id=medicine_id)
                if medicine.stock < quantity:
                    raise ValidationError(
                        f"Not enough stock for {medicine.generic_name}. "
                        f"Available: {medicine.stock}, Requested: {quantity}"
                    )
                    
            except Medicine.DoesNotExist:
                raise ValidationError(f"Medicine with id {medicine_id} does not exist")

    # [OKS] update medicine "stock"
    def _update_medicine_quantities(self, items):
        for item in items:
            medicine = Medicine.objects.get(id=item['item_id'])
            quantity = item['ordered_quantity']
            
            medicine.stock -= quantity
            medicine.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        # [SARA]: Pharmacist can only update status for their store's orders, admin can update all
        if user.role == 'pharmacist':
            allowed_fields = {'order_status'}
            if not set(self.request.data.keys()).issubset(allowed_fields):
                raise PermissionError('Pharmacists can only update order status.')
            

       # [OKS]  Clients can cancel only if order is still pending
        if user.role == 'client':
            requested_status = self.request.data.get('order_status')
            if requested_status != 'cancelled':
                raise PermissionDenied("Clients can only cancel their order.")
            if instance.order_status != 'pending':
                raise PermissionDenied("You can only cancel orders that are still pending.")

        serializer.save()
     # return medicine_stock
    def _return_items_to_stock(self, order):
        with transaction.atomic():
            for item in order.items:
                try:
                    medicine = Medicine.objects.get(id=item['item_id'])
                    medicine.stock += item['ordered_quantity']
                    medicine.save()
                except Medicine.DoesNotExist:
                    logger.error(f"Medicine with id {item['item_id']} not found when returning to stock for order {order.id}")     


    def _send_status_update_notification(self, order, old_status, new_status):
            notification_data = {
                'order': order,
                'old_status': old_status,
                'new_status': new_status,
                'shipping_cost': order.shipping_cost,
                'tax': order.tax,
                'total_with_fees': order.total_with_fees
            }
            send_notification(
                user=order.client.user,
                message=f"Order #{order.id} status changed from {old_status} to {new_status}",
                notification_type='order_update',
                send_email=True,
                email_subject=f"Order #{order.id} Status Update",
                email_template='emails/order_status_update.html',
                email_context=notification_data
            )
            if order.store and order.store.owner:
                send_notification(
                    user=order.store.owner.user,
                    message=f"Order #{order.id} status changed to {new_status}",
                    notification_type='order_update',
                    send_email=True,
                    email_subject=f"Order #{order.id} Status Update",
                    email_template='emails/pharmacist_order_update.html',
                    email_context=notification_data
            )
    # [OKS] Custom action to update order status
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        order = self.get_object()
        old_status = order.order_status
        new_status = request.data.get('status')

        if order.order_status not in ['pending', 'paid']:
            return Response(
                {'error': 'Order status cannot be changed from current state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = ['paid', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Allowed: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status == 'paid':
            if order.payment_method != 'card':
                return Response(
                    {'error': 'Only card payments can be marked as paid directly'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if order.order_status == 'paid':
                return Response(
                    {'error': 'Order is already paid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        order.order_status = new_status
        order.save()

        if old_status != 'cancelled' and new_status == 'cancelled':
            self._return_items_to_stock(order)

        self._send_status_update_notification(order, old_status, new_status)

        return Response({
            'status': 'success',
            'order_id': order.id,
            'new_status': order.order_status,
            'shipping_cost': order.shipping_cost,
            'tax': order.tax,
            'total_with_fees': order.total_with_fees
        })

