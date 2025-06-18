from rest_framework import viewsets
from .models import MedicalDevice, Medicine
from .serializers import MedicalDeviceSerializer, MedicineSerializer

# MEDICAL DEVICE VIEWSET
class MedicalDeviceViewSet(viewsets.ModelViewSet):
    queryset = MedicalDevice.objects.all()
    serializer_class = MedicalDeviceSerializer


# MEDICINE VIEWSET
class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    