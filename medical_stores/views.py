# medical_stores/views.py
from rest_framework import viewsets
from .models import MedicalStore
from .serializers import MedicalStoreSerializer
from .filters import MedicalStoreFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from inventory.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated


# SENU: NEW ADDED
from rest_framework.decorators import action
from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated


class MedicalStoreViewSet(viewsets.ModelViewSet):
    queryset = MedicalStore.objects.all()
    serializer_class = MedicalStoreSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = MedicalStoreFilter
    search_fields = ['store_name', 'store_type']

    permission_classes = [IsAuthenticated]  # Add this if missing

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
