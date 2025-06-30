# medical_stores/filters.py
# [SARA]: Added owner_id filter for MedicalStore API
import django_filters
from .models import MedicalStore

class MedicalStoreFilter(django_filters.FilterSet):
    owner_id = django_filters.NumberFilter(field_name='owner_id')  # Allow filtering by owner_id

    class Meta:
        model = MedicalStore
        fields = ['store_name', 'store_type', 'owner_id']  # Add owner_id to filter fields




