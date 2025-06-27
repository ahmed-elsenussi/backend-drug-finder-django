from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import MedicalDevice, Medicine
from .serializers import MedicalDeviceSerializer, MedicineSerializer
from .permissions import IsPharmacistOwnerOrAdmin, IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models.functions import Lower
from .filters import MedicineFilter


# [SARA]: Custom pagination class with default 12 per page
class DefaultPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'


# ============================
# 🩺 MEDICAL DEVICE VIEWSET
# ============================
class MedicalDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalDeviceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly | IsPharmacistOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['^name', '^brand', '^device_type']  # Use ^ for starts-with filtering
    ordering_fields = ['name', 'brand', 'price', 'stock']  # Fields allowed for sorting
    ordering = ['name']  # Default ordering
    pagination_class = DefaultPagination  # [SARA]: Match frontend itemsPerPage
    filterset_class = None  # No extra filters yet for devices

    # [SARA]: Custom queryset based on user role
    def get_queryset(self):
        user = self.request.user
        queryset = MedicalDevice.objects.select_related('store')  # Optimize joins
        # [SARA]: Admin can see all, pharmacist sees own, client sees all (read-only)
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            return queryset
        if user.role == 'pharmacist':
            return queryset.filter(store__owner__user=user)
        if user.role == 'client':
            return queryset
        return MedicalDevice.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        # [SENU]:DEBUG
        print("Creating Medical Device:")
        print(f"User: {user}")

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


# ====================
# 💊 MEDICINE VIEWSET
# ====================
class MedicineViewSet(viewsets.ModelViewSet):
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly | IsPharmacistOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['^brand_name', '^generic_name', '^chemical_name']  # Use ^ for starts-with filtering
    ordering_fields = ['brand_name', 'generic_name', 'price', 'stock']  # Fields allowed for sorting
    ordering = [Lower('brand_name')]  # Default case-insensitive ordering
    pagination_class = DefaultPagination  # [SARA]: Match frontend itemsPerPage
    filterset_class = MedicineFilter  # [SARA]: Allow filtering by brand_startswith (for A–Z)

    def get_queryset(self):
        user = self.request.user
        queryset = Medicine.objects.select_related('store')  # Optimize database query
        # [SARA]: Admin can see all, pharmacist sees own, client sees all (read-only)
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            return queryset
        if user.role == 'pharmacist':
            return queryset.filter(store__owner__user=user)
        if user.role == 'client':
            return queryset
        return Medicine.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        # [SENU]:DEBUG
        print(f"Create Medicine - User: {user}")
        print(f"Serializer Data: {serializer.validated_data}")

        # [SARA]: Only allow creating for pharmacist's own store
        if user.role == 'pharmacist':
            store = serializer.validated_data.get('store')

            # [SENU]:DEBUG
            print(f"Store: {store}")

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
