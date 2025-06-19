from django.contrib import admin
from .models import MedicalStore

# Register your models here.
# [SARA]: Registered MedicalStore model to appear in the admin panel
admin.site.register(MedicalStore)
