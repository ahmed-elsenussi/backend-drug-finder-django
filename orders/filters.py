# orders/filters.py
# [SARA]: Added OrderFilter for filtering orders by store, order_status, and client
import django_filters
from .models import Order

class OrderFilter(django_filters.FilterSet):
    store = django_filters.NumberFilter(field_name='store_id')  # [SARA]
    order_status = django_filters.CharFilter(field_name='order_status', lookup_expr='iexact')  # [SARA]
    client = django_filters.NumberFilter(field_name='client_id')  # [SARA]
    
    class Meta:
        model = Order
        fields = ['store', 'order_status', 'client']  # [SARA]
