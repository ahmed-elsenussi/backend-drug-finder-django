# medical_stores/filters.py
import django_filters
from .models import MedicalStore

class MedicalStoreFilter(django_filters.FilterSet):
    class Meta:
        model = MedicalStore
        fields = ['store_name', 'store_type']  # ✅ only valid model fields



