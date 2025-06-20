from django.db import models

# Create your models here.
from django.contrib.postgres.fields import JSONField  # or use models.JSONField in Django 3.1+

class Cart(models.Model):
    items = models.JSONField(default=list)  # [{item_id, quantity, price}, ...]
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart #{self.id}"


