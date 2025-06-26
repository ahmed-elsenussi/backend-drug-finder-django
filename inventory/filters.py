import django_filters
from .models import Medicine

class MedicineFilter(django_filters.FilterSet):
    brand_startswith = django_filters.CharFilter(
        field_name="brand_name", lookup_expr="istartswith"
    )

    class Meta:
        model = Medicine
        fields = ['store']  