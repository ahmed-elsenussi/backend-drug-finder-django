from rest_framework import viewsets
from .models import MedicalStore
from .serializers import MedicalStoreSerializer

# MEDICAL DEVICE VIEWSET
class MedicalStoreViewSet(viewsets.ModelViewSet):
    queryset = MedicalStore.objects.all()
    serializer_class = MedicalStoreSerializer