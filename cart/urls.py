from django.urls import path
from .views import CartViewSet

urlpatterns = [
    path('', CartViewSet.as_view({'get': 'list'})),
    path('add/', CartViewSet.as_view({'POST': 'add'})),
  path('update/', CartViewSet.as_view({'put': 'update_quantity'})),
    path('remove/', CartViewSet.as_view({'DELETE': 'remove'})),
]
