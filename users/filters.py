# users/filters.py

import django_filters
from .models import Pharmacist

class PharmacistFilter(django_filters.FilterSet):
    license_status = django_filters.ChoiceFilter(
        field_name='license_status',
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        empty_label='All'
    )

    class Meta:
        model = Pharmacist
        fields = ['license_status']