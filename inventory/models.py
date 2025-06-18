from django.db import models

# MEDICINE MODEL===========
class Medicine(models.Model):

    # mandatory
    stock = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # info for the page
    generic_name = models.CharField(max_length=255)
    brand_name = models.CharField(max_length=255)
    chemical_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    atc_code = models.CharField(max_length=20)
    cas_number = models.CharField(max_length=20)

    # alternatives for the medicines
    alternative_medicines = models.ManyToManyField('self', blank=True)



# MEDICAL DEVICES================
class MedicalDevice(models.Model):

    stock = models.PositiveIntegerField()
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
