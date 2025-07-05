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

    def validate(self, data):
        # If stock is being updated, set is_deleted based on stock value
        if 'stock' in data:
            data['is_deleted'] = data['stock'] <= 0
        return data