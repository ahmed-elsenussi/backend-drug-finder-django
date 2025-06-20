from rest_framework import viewsets
from .models import Order, Cart
from .serializers import OrderSerializer, CartSerializer
from .permissions import OrderAccessPermission
from rest_framework.permissions import IsAuthenticated

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, OrderAccessPermission]

    # [SARA]: Custom queryset based on user role
    def get_queryset(self):
        user = self.request.user
        # [SARA]: Admin can see all, pharmacist sees orders for their stores, client sees their own orders
        if user.is_staff or user.is_superuser:
            return Order.objects.all()
        if user.role == 'pharmacist':
            return Order.objects.filter(store__owner__user=user)
        if user.role == 'client':
            return Order.objects.filter(client__user=user)
        return Order.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        # [SARA]: Pharmacist can only update status for their store's orders, admin can update all
        if user.role == 'pharmacist':
            allowed_fields = {'order_status'}
            if not set(self.request.data.keys()).issubset(allowed_fields):
                raise PermissionError('Pharmacists can only update order status.')
        serializer.save()

    def perform_create(self, serializer):
        user = self.request.user
        # [SARA]: Allow admin to create order for any user, client for self only
        if user.is_staff or user.is_superuser:
            serializer.save()
        elif user.role == 'client':
            # Force the order to be for the logged-in client
            client = getattr(user, 'client', None)
            if not client:
                raise PermissionError('No client profile found for this user.')
            serializer.save(client=client)
        else:
            raise PermissionError('Only clients and admins can create orders.')

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
