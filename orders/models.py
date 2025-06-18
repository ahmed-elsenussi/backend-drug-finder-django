from django.db import models
from users.models import Client


# CART MODEL=================================================================

class Cart(models.Model):

    # array of objects {item_id, ordered_quantity}
    items = models.JSONField(default=list)

    # costs
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # created at ,updated at
    timestamp = models.DateTimeField(auto_now_add=True)


# ORDER MODEL==================================================================
class Order(models.Model):

    # FK: client id
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    # array of objects {item_id, ordered_quantity}
    items = models.JSONField(default=list)

    # location
    shipping_location = models.TextField()

    # choices [SENU]: CHANGED AS [SARA] SAID
    order_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),('paid','Paid'),('on_process', 'On_Process'),('shipping', 'Shipping'), ('delivered', 'Delivered')
    ])
    payment_method = models.CharField(max_length=10, choices=[
        ('cash', 'Cash'),('card', 'Card'),('wallet', 'Wallet')
    ])

    # costs
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # created at, updated at
    timestamp = models.DateTimeField(auto_now_add=True)



#============
'''
fixing the circulation error in the erd:
---------------------------------------
cart ---> client
client ---> cart [removed]

'''

