from rest_framework import serializers
from .models import Order, Cart

# CART SERIALIZER
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'


# ORDER SERIALIZER
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
