from rest_framework import viewsets
from .models import MedicalStore
from .serializers import MedicalStoreSerializer
from inventory.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated

# MEDICAL DEVICE VIEWSET
class MedicalStoreViewSet(viewsets.ModelViewSet):
    queryset = MedicalStore.objects.all()
    serializer_class = MedicalStoreSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]