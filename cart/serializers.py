from rest_framework import serializers
from .models import Cart
from inventory.models import Medicine
from rest_framework.exceptions import ValidationError
from medical_stores.models import MedicalStore 
class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'
        extra_kwargs = {
            'total_price': {'required': False}
        }

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        items = validated_data.get('items', [])
        store_id = validated_data.get('store')
        force_clear = False

        if request:
            force_clear = request.data.get('force_clear', False)

        if not store_id:
            if items:
                try:
                    first_product_id = items[0].get('product')
                    medicine = Medicine.objects.get(id=first_product_id)
                    store_id = medicine.store_id
                    validated_data['store'] = store_id
                except Exception:
                    raise ValidationError({'error': 'store field is required and could not be inferred from items.'})
            else:
                raise ValidationError({'error': 'store field is required.'})

        cart = Cart.objects.filter(user=user).first() if user else None

        if cart and cart.items:
            existing_store_id = None
            for item in cart.items:
                try:
                    med = Medicine.objects.get(id=item.get('product'))
                    if existing_store_id is None:
                        existing_store_id = med.store_id
                    elif med.store_id != existing_store_id:
                        existing_store_id = None
                        break
                except Exception:
                    continue
            if existing_store_id is not None and existing_store_id != store_id:
                if not force_clear:
                    raise ValidationError({
                        'error': 'Cart contains products from another store. Do you want to clear the cart and add this product?',
                        'requires_confirmation': True
                    })
                cart.items = []
                cart.total_price = 0
                cart.save()

        # Merge logic
        updated_items = cart.items.copy() if cart and cart.items else []
        for new_item in items:
            product_id = new_item.get('product')
            quantity = new_item.get('quantity', 1)
            try:
                medicine = Medicine.objects.get(id=product_id)
                if medicine.store_id != store_id:
                    raise ValidationError({'error': f'Product {product_id} does not belong to store {store_id}.'})
            except Medicine.DoesNotExist:
                raise ValidationError({'error': f'Product {product_id} does not exist in store {store_id}.'})
            found = False
            for item in updated_items:
                if item.get('product') == product_id:
                    item['quantity'] = item.get('quantity', 1) + quantity
                    found = True
                    break
            if not found:
                updated_items.append(new_item)

        # Final calculation
        subtotal = 0
        checked_items = []
        for item in updated_items:
            product_id = item.get('product')
            quantity = item.get('quantity', 1)
            try:
                medicine = Medicine.objects.get(id=product_id, store_id=store_id)
            except Medicine.DoesNotExist:
                raise ValidationError({'error': f'Medicine {product_id} not found.'})
            if quantity > medicine.stock:
                raise ValidationError({
                    'error': f'Not enough stock for product {product_id}.'
                })
            subtotal += float(medicine.price) * quantity
            checked_items.append({
                'product': product_id,
                'name': medicine.brand_name,
                'image': medicine.image.url if medicine.image else None,
                'quantity': quantity,
                'price': float(medicine.price),
            })

        validated_data['items'] = checked_items
        validated_data['total_price'] = subtotal + float(validated_data.get('shipping_cost', 0)) + float(validated_data.get('tax', 0))

        if cart:
            validated_data.pop('user', None)
            validated_data.pop('store', None)
            for attr, value in validated_data.items():
                setattr(cart, attr, value)
            cart.save()
            return cart

       
        validated_data.pop('user', None)
        validated_data.pop('store', None)
        store_instance = MedicalStore.objects.get(id=store_id)

        return Cart.objects.create(user=user, store=store_instance, **validated_data)