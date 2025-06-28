# inventory/filters.py
import django_filters
from .models import Medicine

class MedicineFilter(django_filters.FilterSet):
    brand_startswith = django_filters.CharFilter(
        field_name="brand_name", lookup_expr="istartswith"
    )
    store_id = django_filters.NumberFilter(field_name="store__id")

    class Meta:
        model = Medicine
        fields = ['store_id', 'brand_startswith']