from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
# Separate routers
order_router = DefaultRouter()
order_router.register(r'', OrderViewSet, basename='order')  # will be  at /orders/
