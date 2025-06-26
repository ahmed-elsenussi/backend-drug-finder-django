from django.db import models
from users.models import Pharmacist

#  MEDICAL STORES MODEL
class MedicalStore(models.Model):

    # [SENU]: ==========================================================================
    # returns store reviews         ==========>> store.reviews.all() 
    # return the store only         ==========>> GET /api/stores/ → returns stores only
    # return store + its products   ==========>> GET /api/stores/?include_products=true
    #===================================================================================

    # mandatory
    owner = models.ForeignKey(Pharmacist, on_delete=models.CASCADE)
    store_name = models.CharField(max_length=255)
    store_type = models.CharField(max_length=20, choices=[
        ('medical_devices', 'Medical Devices'),('pharmacy', 'Pharmacy'),('both', 'Both')
    ])
    
    license_image = models.ImageField(upload_to='store/licenses/', null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)


    # optionals
    store_logo = models.ImageField(upload_to='store/logos/', null=True, blank=True)
    store_banner = models.ImageField(upload_to='store/banners/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)


    # [SENU], ADD WRITTEN ADDRESS TO BE USED IN THE PROFILE + add phone
    store_address = models.CharField(max_length=250, blank=True, null=True)
    phone  = models.CharField(max_length=15, blank=True, null=True)



    # [SENU] New fields for opening and closing times
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)


    # [SARA]: Removed ManyToMany fields for medicines and devices, as each product instance is unique to a store
    # medicines = models.ManyToManyField(Medicine, blank=True)
    # devices = models.ManyToManyField(MedicalDevice, blank=True)

    # [OKS] add lang and lat for the store
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # --print---------

    def __str__(self):
        return f"{self.store_name} ({self.store_type})"

