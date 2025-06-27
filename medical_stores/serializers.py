from rest_framework import serializers
from .models import MedicalStore
from inventory.serializers import MedicineSerializer, MedicalDeviceSerializer

# MEDICAL STORE SERIALIZER
class MedicalStoreSerializer(serializers.ModelSerializer):
    #[OKS] add medicine to the serializer
    medicines = serializers.SerializerMethodField()

    class Meta:
        model = MedicalStore
        fields = '__all__'

     
    # [SENU] TO GET MEDCIINES IN CASE YOU NEED IT
    def get_medicines(self, obj):
        request = self.context.get('request')
        matched_medicines = self.context.get('matched_medicines', {})

        # If store has matched medicines from the view
        if obj.id in matched_medicines:
            medicines = matched_medicines[obj.id]
            return MedicineSerializer(medicines, many=True, context={'request': request}).data
        return []
    # [SENU] TO GET MEDICAL DEVICES IN CASE YOU NEED IT
    def get_medical_devices(self, obj):
        request = self.context.get('request')
        if request and request.query_params.get('include_products') == 'true':
            return MedicalDeviceSerializer(obj.medical_devices.all(), many=True).data
        return None