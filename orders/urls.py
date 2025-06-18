from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CartViewSet

# Separate routers
order_router = DefaultRouter()
order_router.register(r'', OrderViewSet, basename='order')  # will be  at /orders/

cart_router = DefaultRouter()
cart_router.register(r'', CartViewSet, basename='cart')  # will be  at /cart/
