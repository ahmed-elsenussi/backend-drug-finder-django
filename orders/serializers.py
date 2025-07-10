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
        request = self.context.get('request', None)  # [SARA] Get request for absolute URI
        results = []
        for item in obj.items:
            item_id = item.get('item_id')
            price = item.get('price')
            quantity = item.get('ordered_quantity')

            try:
                medicine = Medicine.objects.get(id=item_id)
                # [SARA] Use absolute URI for image
                if medicine.image and request is not None:
                    image_url = request.build_absolute_uri(medicine.image.url)
                else:
                    image_url = medicine.image.url if medicine.image else None
                results.append({
                    "name": medicine.brand_name,
                    "price": price,
                    "image": image_url,
                    "quantity": quantity
                })
            except Medicine.DoesNotExist:
                continue  # Skip if not a Medicine

        return results
