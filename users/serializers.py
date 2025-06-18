from rest_framework import serializers
from .models import User, Client, Pharmacist

# USER SERAILZIER
class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

# CLIENT SERIALIZER
class ClientSerializers(serializers.ModelSerializer):

    # mirror the name from the user table
    name = serializers.CharField(source='user.name', read_only= True)
    user_id = serializers.IntegerField(source='user.id', read_only = True)

    class Meta:
        model = Client
        fields = '__all__'
    

# PHARAMCIST SERIALIZER
class PharmacistSerializers(serializers.ModelSerializer):

    # mirror the name from the user table
    name = serializers.CharField(source='user.name', read_only= True)
    user_id = serializers.IntegerField(source='user.id', read_only = True)
    
    class Meta:
        model = Pharmacist
        fields = '__all__'