from django.db import models
from users.models import Client
from medical_stores.models import MedicalStore


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
    # [SARA]: Add store_id referencing MedicalStore
    store = models.ForeignKey(MedicalStore, on_delete=models.CASCADE, null=True, blank=True)

    # array of objects {item_id, ordered_quantity}
    items = models.JSONField(default=list)

    # location
    shipping_location = models.TextField()

    # choices [SENU]: CHANGED AS [SARA] SAID
    order_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),('paid','Paid'),('on_process', 'On_Process'),('shipping', 'Shipping'), ('delivered', 'Delivered'), ('canceled', 'Canceled')
    ])
    payment_method = models.CharField(max_length=10, choices=[
        ('cash', 'Cash'),('card', 'Card'),('wallet', 'Wallet')
    ])

    # costs
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_with_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)



    # created at, updated at
    timestamp = models.DateTimeField(auto_now_add=True)



#============
'''
fixing the circulation error in the erd:
---------------------------------------
cart ---> client
client ---> cart [removed]

'''

# Add these models to your models.py
class ShippingConfig(models.Model):
    """[OKS] Model to store shipping cost configurations"""
    name = models.CharField(max_length=100)
    max_distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    cost = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['max_distance_km']
        
    def __str__(self):
        return f"{self.name} (up to {self.max_distance_km}km): ${self.cost}"

class TaxConfig(models.Model):
    """[OKS] Model to store tax rate configurations"""
    region_name = models.CharField(max_length=100)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4)  # Stores 0.0825 for 8.25%
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Tax Configurations"
        
    def __str__(self):
        return f"{self.region_name} ({float(self.tax_rate)*100:.2f}%)"

# Then update your OrderViewSet methods: