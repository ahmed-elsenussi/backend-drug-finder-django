from rest_framework import serializers
from .models import Cart
from inventory.models import Medicine
from rest_framework.exceptions import ValidationError
from medical_stores.models import MedicalStore
from decimal import Decimal

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
        force_clear = request.data.get('force_clear', False) if request else False

        # Infer store_id from first item if not provided
        if not store_id and items:
            try:
                first_product_id = items[0].get('product')
                medicine = Medicine.objects.get(id=first_product_id)
                store_id = medicine.store_id
                validated_data['store'] = store_id
            except Medicine.DoesNotExist:
                raise ValidationError({'error': f'Product {first_product_id} does not exist.'})
            except Exception:
                raise ValidationError({'error': 'store field is required and could not be inferred from items.'})
        elif not store_id:
            raise ValidationError({'error': 'store field is required.'})

        store_instance = MedicalStore.objects.get(id=store_id)
        cart = Cart.objects.filter(user=user).first() if user else None

        # Handle store conflict
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
                except Medicine.DoesNotExist:
                    continue
            if existing_store_id is not None and existing_store_id != store_id:
                if not force_clear:
                    raise ValidationError({
                        'error': 'Cart contains products from another store. Do you want to clear the cart and add this product?',
                        'requires_confirmation': True
                    })
                cart.items = []
                cart.total_price = Decimal('0.00')
                cart.save()

        # Update or initialize items
        updated_items = cart.items.copy() if cart and cart.items else []
        for new_item in items:
            product_id = new_item.get('product')
            quantity = new_item.get('quantity', 1)
            try:
                medicine = Medicine.objects.get(id=product_id)
            except Medicine.DoesNotExist:
                raise ValidationError({'error': f'Product {product_id} does not exist.'})

            found = False
            for item in updated_items:
                if item.get('product') == product_id:
                    # Add new quantity to existing quantity
                    new_total_quantity = item.get('quantity', 0) + quantity
                    if new_total_quantity > medicine.stock:
                        raise ValidationError({
                            'error': f'Not enough stock for product {product_id}. Available: {medicine.stock}, requested: {new_total_quantity}'
                        })
                    item['quantity'] = new_total_quantity
                    found = True
                    break
            if not found:
                if quantity > medicine.stock:
                    raise ValidationError({
                        'error': f'Not enough stock for product {product_id}. Available: {medicine.stock}, requested: {quantity}'
                    })
                updated_items.append({
                    'product': product_id,
                    'quantity': quantity
                })

        # Calculate subtotal and prepare checked items
        subtotal = Decimal('0.00')
        checked_items = []
        for item in updated_items:
            product_id = item.get('product')
            quantity = item.get('quantity', 1)
            try:
                medicine = Medicine.objects.get(id=product_id)
            except Medicine.DoesNotExist:
                raise ValidationError({'error': f'Medicine {product_id} not found.'})
            if quantity > medicine.stock:
                raise ValidationError({
                    'error': f'Not enough stock for product {product_id}. Available: {medicine.stock}, requested: {quantity}'
                })
            item_subtotal = Decimal(str(medicine.price)) * Decimal(str(quantity))
            subtotal += item_subtotal
            checked_items.append({
                'product': product_id,
                'name': medicine.brand_name,
                'image': request.build_absolute_uri(medicine.image.url) if medicine.image and request else None,
                'quantity': quantity,
                'price': float(medicine.price),
            })

        # Set validated_data with calculated fields
        validated_data['items'] = checked_items
        validated_data['total_price'] = subtotal + Decimal(str(validated_data.get('shipping_cost', '0.00'))) + Decimal(str(validated_data.get('tax', '0.00')))
        validated_data['user'] = user
        validated_data['store'] = store_instance

        if cart:
            # Update existing cart
            for attr, value in validated_data.items():
                setattr(cart, attr, value)
            cart.save()
            return cart

        # Create new cart
        return Cart.objects.create(**validated_data)