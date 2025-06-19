from rest_framework import viewsets
from .models import MedicalDevice, Medicine
from .serializers import MedicalDeviceSerializer, MedicineSerializer
from .permissions import IsPharmacistOwnerOrAdmin
from rest_framework.permissions import IsAuthenticated

# MEDICAL DEVICE VIEWSET
class MedicalDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalDeviceSerializer
    permission_classes = [IsAuthenticated, IsPharmacistOwnerOrAdmin]

    # [SARA]: Custom queryset based on user role
    def get_queryset(self):
        user = self.request.user
        # [SARA]: Admin can see all, pharmacist sees own, client sees all (read-only)
        if user.is_staff or user.is_superuser:
            return MedicalDevice.objects.all()
        if user.role == 'pharmacist':
            return MedicalDevice.objects.filter(store__owner__user=user)
        if user.role == 'client':
            return MedicalDevice.objects.all()
        return MedicalDevice.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        # [SARA]: Only allow creating for pharmacist's own store
        if user.role == 'pharmacist':
            store = serializer.validated_data.get('store')
            if not store or store.owner.user != user:
                raise PermissionError('You can only add devices to your own store.')
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        # [SARA]: Only allow updating for pharmacist's own store
        if user.role == 'pharmacist':
            store = serializer.validated_data.get('store', getattr(self.get_object(), 'store', None))
            if not store or store.owner.user != user:
                raise PermissionError('You can only update devices in your own store.')
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        # [SARA]: Only allow deleting for pharmacist's own store
        if user.role == 'pharmacist':
            if not instance.store or instance.store.owner.user != user:
                raise PermissionError('You can only delete devices from your own store.')
        instance.delete()

# MEDICINE VIEWSET
class MedicineViewSet(viewsets.ModelViewSet):
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated, IsPharmacistOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        # [SARA]: Admin can see all, pharmacist sees own, client sees all (read-only)
        if user.is_staff or user.is_superuser:
            return Medicine.objects.all()
        if user.role == 'pharmacist':
            return Medicine.objects.filter(store__owner__user=user)
        if user.role == 'client':
            return Medicine.objects.all()
        return Medicine.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        # [SARA]: Only allow creating for pharmacist's own store
        if user.role == 'pharmacist':
            store = serializer.validated_data.get('store')
            if not store or store.owner.user != user:
                raise PermissionError('You can only add medicines to your own store.')
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        # [SARA]: Only allow updating for pharmacist's own store
        if user.role == 'pharmacist':
            store = serializer.validated_data.get('store', getattr(self.get_object(), 'store', None))
            if not store or store.owner.user != user:
                raise PermissionError('You can only update medicines in your own store.')
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        # [SARA]: Only allow deleting for pharmacist's own store
        if user.role == 'pharmacist':
            if not instance.store or instance.store.owner.user != user:
                raise PermissionError('You can only delete medicines from your own store.')
        instance.delete()
