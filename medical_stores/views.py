# medical_stores/views.py
from rest_framework import viewsets
from .models import MedicalStore
from .serializers import MedicalStoreSerializer
from .filters import MedicalStoreFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

class MedicalStoreViewSet(viewsets.ModelViewSet):
    queryset = MedicalStore.objects.all()
    serializer_class = MedicalStoreSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = MedicalStoreFilter

    search_fields = ['store_name', 'store_type']
