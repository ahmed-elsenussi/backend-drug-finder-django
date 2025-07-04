from django.contrib import admin
from .models import User ,Client, Pharmacist, Delivery
# Register your models here.
admin.site.register(User)
admin.site.register(Client)
admin.site.register(Pharmacist)
admin.site.register(Delivery)
