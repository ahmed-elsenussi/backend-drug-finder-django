from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Cart
from .serializers import CartSerializer
from inventory.models import Medicine
from decimal import Decimal

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow users to access their own cart
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the cart is always linked to the authenticated user
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_items(self, request, pk=None):
        cart = self.get_object()
        new_items = request.data.get("items", [])
        updated_items = cart.items.copy() if cart.items else []
        for new_item in new_items:
            product_id = new_item.get("product")
            quantity = new_item.get("quantity", 1)
            found = False
            for idx, item in enumerate(updated_items):
                if item.get("product") == product_id:
                    # If quantity is positive, increase; if negative, decrease
                    new_qty = item.get("quantity", 1) + quantity
                    if new_qty > 0:
                        updated_items[idx]["quantity"] = new_qty
                    else:
                        updated_items.pop(idx)
                    found = True
                    break
            if not found and quantity > 0:
                updated_items.append({"product": product_id, "quantity": quantity})
        # Validate and recalculate subtotal
        subtotal = 0
        checked_items = []
        store_id = None
        for item in updated_items:
            product_id = item.get("product")
            quantity = item.get("quantity", 1)
            try:
                medicine = Medicine.objects.get(id=product_id)
                price = float(medicine.price)
                if store_id is None:
                    store_id = medicine.store_id
                elif medicine.store_id != store_id:
                    return Response({'error': 'All products must be from the same store.'}, status=status.HTTP_400_BAD_REQUEST)
                if quantity > medicine.stock:
                    return Response({
                        'error': f'Not enough stock for product {product_id}. Available: {medicine.stock}, requested: {quantity}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Medicine.DoesNotExist:
                price = 0
            subtotal += price * quantity
            checked_items.append({**item, "price": price})
        cart.items = checked_items
        cart.total_price = Decimal(str(subtotal)) + cart.shipping_cost + cart.tax
        cart.save()
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['patch'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product')
        if product_id is None:
            return Response({'error': 'Product ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        # Remove item(s) with the given product ID
        updated_items = []
        for item in cart.items:
            if item.get('product') == product_id:
                # If quantity is provided, decrease it, else remove
                remove_qty = request.data.get('quantity')
                if remove_qty is not None:
                    current_qty = item.get('quantity', 1)
                    if current_qty > remove_qty:
                        item['quantity'] = current_qty - remove_qty
                        updated_items.append(item)
                    # else: don't append, item is removed
                # If no quantity provided, remove the item completely
                continue
            updated_items.append(item)
        # Recalculate subtotal
        subtotal = sum(Decimal(str(item['price'])) * item.get('quantity', 1) for item in updated_items)
        cart.items = updated_items
        cart.total_price = subtotal + cart.shipping_cost + cart.tax
        cart.save()
        return Response(CartSerializer(cart).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'cart deleted'}, status=status.HTTP_200_OK)
