from django.db import models
from users.models import Client
from orders.models import Order

class Payment(models.Model):

    # order id FK + client id FK
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # choices
    payment_method = models.CharField(max_length=10, choices=[('cash', 'Cash'),('card', 'Card'),])
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'),('completed', 'Completed'),('failed', 'Failed')])
    payment_date = models.DateTimeField(auto_now_add=True)
