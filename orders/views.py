from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.conf import settings
import stripe
from rest_framework.decorators import action

from .models import Order
from cart.models import Cart
from payments.models import Payment
from .serializers import OrderSerializer, CartSerializer
from .permissions import OrderAccessPermission


stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, OrderAccessPermission]
    # [SARA]: Custom queryset based on user role
    def get_queryset(self):
        user = self.request.user
        # [SARA]: Admins can see all orders, pharmacists see their store's orders, clients see their own orders
        if user.is_staff or user.is_superuser:
            return Order.objects.all()
        if user.role == 'pharmacist':
            return Order.objects.filter(store__owner__user=user)
        if user.role == 'client':
            return Order.objects.filter(client__user=user)
        return Order.objects.none()
    #[OKS] change name to create
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        payment_method = data.get("payment_method", "cash")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # [SARA]: Allow admin to create order for any user, client for self only
        if user.is_staff or user.is_superuser:
            order = serializer.save()
            cart_user = user
        elif user.role == 'client':
            client = getattr(user, 'client', None)
            if not client:
                raise PermissionError('No client profile found for this user.')
            order = serializer.save(client=client)
            cart_user = client.user  # [OKS] get the user from the client relation
        else:
            raise PermissionError('Only clients and admins can create orders.')

        # [OKS] Remove the user's cart safely
        try:
            Cart.objects.get(user=cart_user).delete()
        except Cart.DoesNotExist:
            pass  # no cart to delete

        # [OKS] Create Payment record
        Payment.objects.create(
            order=order,
            client=order.client,
            amount=order.total_price,
            payment_method=payment_method,
            status='pending' if payment_method == 'cash' else 'initiated'
        )

        response_data = {
            'order': OrderSerializer(order).data
        }

        # [OKS] Handle Stripe if needed
        if payment_method == 'cash':
            order.order_status = 'pending'
            order.save()
        elif payment_method == 'card':
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(order.total_price * 100),
                    currency='usd',
                    metadata={'order_id': order.id},
                    payment_method_types=['card'],
                    # Add this to automatically capture payment
                    capture_method='automatic'
                )
                response_data['client_secret'] = intent.client_secret
        
        #[OKS] Check if payment was immediately successful (like with saved cards)
                if intent.status == 'succeeded':
                    order.order_status = 'paid'
                    order.save()
            
            except Exception as e:
             raise ValidationError(f"Stripe error: {str(e)}")
        else:
            raise ValidationError('Invalid payment method.')

        return Response(response_data, status=status.HTTP_201_CREATED)



    def perform_update(self, serializer):
        user = self.request.user
        # [SARA]: Pharmacist can only update status for their store's orders, admin can update all
        if user.role == 'pharmacist':
            allowed_fields = {'order_status'}
            if not set(self.request.data.keys()).issubset(allowed_fields):
                raise PermissionError('Pharmacists can only update order status.')
        serializer.save()

    # [OKS] Custom action to update order status
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Custom action to update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        # Validate status transition
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
        
        # Special validation for paid status
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
        
        # Update status
        order.order_status = new_status
        order.save()
        
        return Response({
            'status': 'success',
            'order_id': order.id,
            'new_status': order.order_status
        })


    
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
