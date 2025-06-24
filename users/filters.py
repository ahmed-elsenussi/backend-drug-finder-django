# users/filters.py

import django_filters
from .models import Pharmacist

class PharmacistFilter(django_filters.FilterSet):
    is_approved = django_filters.BooleanFilter(field_name='is_approved')

    class Meta:
        model = Pharmacist
        fields = ['is_approved']
