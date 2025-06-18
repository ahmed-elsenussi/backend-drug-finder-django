from rest_framework import serializers
from .models import MedicalDevice, Medicine


# MEDICAL DEVICE SERIALIZER
class MedicalDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalDevice
        fields = '__all__'


# MEDICINE SERIALIZER
class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'
