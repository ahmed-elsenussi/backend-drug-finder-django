from django.urls import path
from .views import CartViewSet

cart_list = CartViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

cart_detail = CartViewSet.as_view({
    'get': 'retrieve',
    'patch': 'update',
    'delete': 'destroy'
})

urlpatterns = [
    path('cart/', cart_list, name='cart-list'),
    path('cart/<int:pk>/', cart_detail, name='cart-detail'),
    path('cart/<int:pk>/update-items/', CartViewSet.as_view({'patch': 'update_items'}), name='update-cart-items'),
    path('cart/<int:pk>/remove-item/', CartViewSet.as_view({'patch': 'remove_item'}), name='remove-cart-item'),
    path('cart/<int:pk>/delete/', CartViewSet.as_view({'delete': 'destroy'}), name='cart-delete'),
]
