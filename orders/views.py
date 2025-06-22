from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.conf import settings
import stripe
from .models import Order, Cart
from .serializers import OrderSerializer, CartSerializer
from .permissions import OrderAccessPermission
from payments.models import Payment
from inventory.permissions import IsAdminCRU

stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderViewSet(viewsets.ModelViewSet):
    # [SARA]: Use OrderSerializer for all order operations
    serializer_class = OrderSerializer
    # [SARA]: Admins (IsAdminCRU) can CRU, others use OrderAccessPermission
    permission_classes = [IsAuthenticated, IsAdminCRU | OrderAccessPermission]

    # [SARA]: Custom queryset based on user role
    def get_queryset(self):
        user = self.request.user
        # [SARA]: Admins can see all orders, pharmacists see their store's orders, clients see their own orders
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            return Order.objects.all()
        if user.role == 'pharmacist':
            return Order.objects.filter(store__owner__user=user)
        if user.role == 'client':
            return Order.objects.filter(client__user=user)
        return Order.objects.none()

    # [OKS] change name to create
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        payment_method = data.get("payment_method", "cash")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # [SARA]: Allow admin to create order for any user, client for self only
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            order = serializer.save()
        elif user.role == 'client':
            client = getattr(user, 'client', None)
            if not client:
                raise PermissionError('No client profile found for this user.')
            order = serializer.save(client=client)
        else:
            raise PermissionError('Only clients and admins can create orders.')

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

        # [OK] handel stripe
        # [SARA]: Handle Stripe payment if needed
        if payment_method == 'cash':
            order.order_status = 'pending'
            order.save()
        elif payment_method == 'card':
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(order.total_price * 100),
                    currency='usd',
                    metadata={'order_id': order.id}
                )
                response_data['client_secret'] = intent.client_secret
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

# [SARA]: CartViewSet for cart operations
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
