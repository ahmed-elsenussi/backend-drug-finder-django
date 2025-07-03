# medical_stores/views.py
from rest_framework import viewsets
from .models import MedicalStore
from .serializers import MedicalStoreSerializer
from .filters import MedicalStoreFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
#[OKS]  import necessary modules for fetching medical store  with medicine inventory
from rest_framework.decorators import action
from rest_framework.response import Response
from inventory.models import Medicine 
from django.db.models import Q
from rest_framework import serializers



from inventory.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated


# SENU: NEW ADDED
from rest_framework.decorators import action
from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated


class MedicalStoreViewSet(viewsets.ModelViewSet):
    #[AMS]:- Only show stores where pharmacist's license is approved
    queryset = MedicalStore.objects.filter(owner__license_status='approved')
    serializer_class = MedicalStoreSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = MedicalStoreFilter
    search_fields = ['store_name', 'store_type']
    medicines = serializers.SerializerMethodField() 
    permission_classes=[IsAuthenticated]
    # [AMS]:- to make admin can see all stores 
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()  # Starts with approved stores only
        
        # Admins can see all stores regardless of license status
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            return MedicalStore.objects.all()
            
        # Pharmacists can only see their own stores
        if user.role == 'pharmacist':
            return queryset.filter(owner__user=user)
            
        # Clients see only approved stores (default queryset already handles this)
        return queryset



    def perform_create(self, serializer):
        store = serializer.save()

        # ✅ Update the pharmacist after store creation
        user = self.request.user
        if hasattr(user, 'pharmacist'):
            pharmacist = user.pharmacist
            pharmacist.has_store = True

            # Ensure it's a list and append
            if not pharmacist.medical_stores_ids:
                pharmacist.medical_stores_ids = []

            if store.id not in pharmacist.medical_stores_ids:
                pharmacist.medical_stores_ids.append(store.id)

            pharmacist.save()

    @action(detail=False, methods=['get'], url_path='my-store')
    def my_store(self, request):
        pharmacist = request.user.pharmacist
        try:
            store = MedicalStore.objects.get(owner=pharmacist)
        except MedicalStore.DoesNotExist:
            return Response({'detail': 'No store found for this pharmacist'}, status=404)

        serializer = self.get_serializer(store)
        return Response(serializer.data)
    

    #[OKS] method search for pharmacies with a specific medicine
    @action(detail=False, methods=['get'], url_path='with-medicine')
    def stores_with_medicine(self, request, format=None): 
        medicine_name = request.query_params.get('medicine_name')

        if not medicine_name:
            return Response({'error': 'medicine_name parameter is required'}, status=400)
          
         #[OKS] not case insensitive search 
        matched_medicines = Medicine.objects.filter(
        Q(brand_name__iexact=medicine_name) | Q(generic_name__iexact=medicine_name)
        ).select_related('store')
        
        store_to_medicines = {}
        for med in matched_medicines:
            store_id = med.store.id  
            store_to_medicines.setdefault(store_id, []).append(med)
        store_ids = list(store_to_medicines.keys())
        stores = MedicalStore.objects.filter(id__in=store_ids)
        serializer = self.get_serializer(
         stores, many=True, 
         context={'request': request, 'matched_medicines': store_to_medicines}
        )
        return Response(serializer.data)
