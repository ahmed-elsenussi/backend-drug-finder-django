from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Cart, CartItem, Product
from .serializers import CartSerializer, CartItemSerializer
# NOTE: Remove IsAuthenticated for now if you don’t want auth
# from rest_framework.permissions import IsAuthenticated

class CartViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]  # Optional

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def add(self, request):
        product_id = request.data['product_id']
        quantity = int(request.data.get('quantity', 1))
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product = Product.objects.get(id=product_id)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
        return Response({'status': 'added'}, status=201)

    def update_quantity(self, request):
        item_id = request.data['item_id']
        quantity = int(request.data['quantity'])
        try:
            item = CartItem.objects.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        item.quantity = quantity
        item.save()
        return Response({'status': 'updated'})

    def remove(self, request):
        item_id = request.data['item_id']
        try:
            item = CartItem.objects.get(id=item_id)
            item.delete()
            return Response({'status': 'removed'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
