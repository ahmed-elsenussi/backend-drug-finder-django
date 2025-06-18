from rest_framework import viewsets
from .models import User, Client, Pharmacist
from .serializers import UserSerializers, ClientSerializers, PharmacistSerializers

# USER VIEWSET
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializers


# CLIENT VIEWSET
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializers


# PHARMACIST VIEWSET
class PharmacistViewSet(viewsets.ModelViewSet):
    queryset = Pharmacist.objects.all()
    serializer_class = PharmacistSerializers