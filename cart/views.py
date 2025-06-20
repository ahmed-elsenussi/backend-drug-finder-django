from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Cart
from .serializers import CartSerializer

class CartViewSet(viewsets.ViewSet):

    def list(self, request):
        carts = Cart.objects.all()
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            cart = Cart.objects.get(pk=pk)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=404)

    def create(self, request):
        data = request.data
        items = data.get('items', [])
        tax = float(data.get('tax', 0))
        shipping = float(data.get('shipping_cost', 0))
        total = sum(item['price'] * item['quantity'] for item in items) + tax + shipping

        cart = Cart.objects.create(
            items=items,
            tax=tax,
            shipping_cost=shipping,
            total_price=total
        )
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=201)

    def update(self, request, pk=None):
        try:
            cart = Cart.objects.get(pk=pk)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=404)

        data = request.data
        items = data.get('items', cart.items)
        tax = float(data.get('tax', cart.tax))
        shipping = float(data.get('shipping_cost', cart.shipping_cost))
        total = sum(item['price'] * item['quantity'] for item in items) + tax + shipping

        cart.items = items
        cart.tax = tax
        cart.shipping_cost = shipping
        cart.total_price = total
        cart.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        try:
            cart = Cart.objects.get(pk=pk)
            cart.delete()
            return Response({'message': 'Cart deleted'})
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=404)
