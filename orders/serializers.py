from rest_framework import serializers
from .models import Order, Cart
from inventory.models import Medicine, MedicalDevice

# CART SERIALIZER
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'


# ORDER SERIALIZER


class OrderSerializer(serializers.ModelSerializer):
    items_details = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'
        depth = 1

    def get_items_details(self, obj):
        results = []
        for item in obj.items:
            item_id = item.get('item_id')
            quantity = item.get('ordered_quantity')

            product = None
            try:
                product = Medicine.objects.get(id=item_id)
            except Medicine.DoesNotExist:
                try:
                    product = MedicalDevice.objects.get(id=item_id)
                except MedicalDevice.DoesNotExist:
                    continue  # skip if neither found

            results.append({
                "name": getattr(product, "brand_name", getattr(product, "model_number", "Unknown")),
                "price": product.price,
                "quantity": quantity
            })

        return results