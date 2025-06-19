from django.contrib import admin
from .models import MedicalDevice, Medicine

# Register your models here.
admin.site.register(MedicalDevice)
admin.site.register(Medicine)
