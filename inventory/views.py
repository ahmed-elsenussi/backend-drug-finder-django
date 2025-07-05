from rest_framework import viewsets, filters, generics
from django_filters.rest_framework import DjangoFilterBackend
from .models import MedicalDevice, Medicine
from .serializers import MedicalDeviceSerializer, MedicineSerializer
from .permissions import IsPharmacistOwnerOrAdmin, IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models.functions import Lower
from .filters import MedicineFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

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
            # [AMS]:- fix logic here to Exclude medicines from stores where pharmacist has pending license status
            return queryset.filter(store__owner__license_status='approved')
            # ####################
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
        # [SENU]: Filter out soft-deleted medicines by default
        queryset = Medicine.objects.select_related('store').filter(is_deleted=False)
        # [SARA]: Admin can see all, pharmacist sees own, client sees all (read-only)
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            return queryset
        if user.role == 'pharmacist':
            return queryset.filter(store__owner__user=user)
        if user.role == 'client':
            # [AMS]:- fix logic here to Exclude medicines from stores where pharmacist has pending license status
            # Only include devices from stores where the pharmacist is approved
            return queryset.filter(store__owner__license_status='approved')
        return Medicine.objects.none()

    def get_object(self):
        """
        Override to allow accessing soft-deleted medicines for update actions.
        """
        user = self.request.user
        queryset = Medicine.objects.select_related('store')
        # For update actions, allow pharmacists to access soft-deleted medicines in their store
        if self.action == 'update' or self.action == 'partial_update':
            if user.role == 'pharmacist':
                queryset = queryset.filter(store__owner__user=user)
        else:
            # Default behavior: exclude soft-deleted medicines
            queryset = queryset.filter(is_deleted=False)
            if user.role == 'pharmacist':
                queryset = queryset.filter(store__owner__user=user)
            elif user.role == 'client':
                queryset = queryset.filter(store__owner__license_status='approved')
            elif not (user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin'):
                queryset = Medicine.objects.none()

        obj = generics.get_object_or_404(queryset, pk=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

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
        # [SENU]:DEBUG
        print(f"Updating Medicine - User: {user}, Data: {serializer.validated_data}")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        # [SARA]: Only allow deleting for pharmacist's own store
        if user.role == 'pharmacist':
            if not instance.store or instance.store.owner.user != user:
                raise PermissionError('You can only delete medicines from your own store.')
        # [SENU]: Implement soft delete by setting is_deleted to True
        instance.is_deleted = True
        instance.stock = 0
        instance.save()

    # FOR ADMIN YA SARAAAAAAAAAAAAAAAAAAA
    # [SENU]: Endpoint to retrieve soft-deleted medicines
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def deleted(self, request):
        """Endpoint to retrieve all soft-deleted medicines"""
        print("DEBUG: Reached deleted endpoint")  # [SENU]: Debug
        queryset = Medicine.objects.select_related('store').filter(is_deleted=True)
        print(f"DEBUG: Queryset count: {queryset.count()}")  # [SENU]: Debug
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # FOR THE PHARAMACIST TO GET THE DATA OF THE DELETED MEDICINE FOR HIS STORE
    # [SENU]: New endpoint to retrieve soft-deleted medicines for a specific store
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def deleted_by_store(self, request):
        """Endpoint to retrieve soft-deleted medicines for a specific store"""
        store_id = request.query_params.get('store_id')
        print(f"DEBUG: Reached deleted_by_store endpoint, store_id: {store_id}")  # [SENU]: Debug
        queryset = Medicine.objects.select_related('store').filter(is_deleted=True).order_by(Lower('brand_name'))
        
        if store_id:
            try:
                store_id = int(store_id)
                queryset = queryset.filter(store__id=store_id)
                print(f"DEBUG: Filtered by store_id={store_id}, count: {queryset.count()}")  # [SENU]: Debug
            except ValueError:
                return Response({"detail": "Invalid store_id. It must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "store_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # [NEW ENDPOINT] FOR ARCHIVED AND OUT-OF-STOCK MEDICINES
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def archived_out_of_stock(self, request):
        """Endpoint to retrieve medicines that are both archived (is_deleted=True) AND out of stock (stock=0)"""
        store_id = request.query_params.get('store_id')
        print(f"DEBUG: Reached archived_out_of_stock endpoint, store_id: {store_id}")  # [SENU]: Debug
        
        # Filter for both conditions
        queryset = Medicine.objects.select_related('store').filter(
            is_deleted=True,
            stock=0
        )
        
        if store_id:
            try:
                store_id = int(store_id)
                queryset = queryset.filter(store__id=store_id)
                print(f"DEBUG: Filtered by store_id={store_id}, count: {queryset.count()}")  # [SENU]: Debug
            except ValueError:
                return Response({"detail": "Invalid store_id. It must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)