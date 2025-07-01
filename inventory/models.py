from django.db import models
from medical_stores.models import MedicalStore

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

    # [SARA]: Added price and store ForeignKey to MedicalStore for unique inventory per store
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    store = models.ForeignKey(MedicalStore, on_delete=models.CASCADE, null=True, blank=True)

    # [SARA]: Added image field for medicine
    image = models.ImageField(upload_to='medicine/images/', null=True, blank=True)


    # TO FAST THE SORTING
    # ====================
    class Meta:
        indexes = [
            models.Index(fields=['brand_name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['chemical_name']),
        ]
    # [AMS]: Add STR method to present the Medicine in a human-readable format
    def __str__(self):
        return f"{self.brand_name} - {self.generic_name}"

# MEDICAL DEVICES================
class MedicalDevice(models.Model):
    stock = models.PositiveIntegerField()
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # [SARA]: Added price and store ForeignKey to MedicalStore for unique inventory per store
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    store = models.ForeignKey(MedicalStore, on_delete=models.CASCADE, null=True, blank=True)

    # [SARA]: Added image field for medical device
    image = models.ImageField(upload_to='medicaldevice/images/', null=True, blank=True)
    
    
    # [AMS]: Add STR method to present the device in a human-readable format
    def __str__(self):
        return f"{self.model_number} - {self.serial_number}"