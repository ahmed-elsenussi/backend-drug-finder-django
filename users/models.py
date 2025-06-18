from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

# USER MODEL=========================================================

# Custom User Manager (Required for email-based login)
class UserManager(BaseUserManager):

    # TELL DJANGO HOW TO CREATE THE USER
    def create_user(self, email, name, password=None, **extra_fields):

        # EMAIL MANDATORY
        if not email:
            raise ValueError('Users must have an email address')
        
        # EMAIL, NAME, PASSWORD
        user = self.model( email=self.normalize_email(email), name=name,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # OVERRIDE CREATING ADMIN
    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    # fields
    name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for admin access
    
    role = models.CharField(max_length=10, choices=[
        ('guest', 'Guest'),('client', 'Client'),
        ('pharmacist', 'Pharmacist'),('admin', 'Admin')
    ], default='guest')

    # use email as username
    username = None  # rm username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    # [SENU]: adding the group and the permsision by this way reduce the performance of fetching the users

    # printing--------------------------------------------
    def __str__(self):
        return f"Doctor: {self.name} - email: {self.email}"

# CLIENT MODEL==========================================================

class Client(models.Model):
    # id for USER: FK,(PK)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    
    # images
    image_profile = models.ImageField(upload_to='pharmacist/profile/', null=True, blank=True)
    
    # addresses
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    default_latitude = models.FloatField(null=True, blank=True)
    default_longitude = models.FloatField(null=True, blank=True)
    
    # optionals
    info_disease = models.TextField(null=True, blank=True)
    is_verified_purchase = models.BooleanField(default=False)

# PHARMACIST MODEL======================================================

class Pharmacist(models.Model):
    # id for USER: FK,(PK)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    
    # images
    image_profile = models.ImageField(upload_to='pharmacist/profile/')
    image_license = models.ImageField(upload_to='pharmacist/license/')
    
    # for performance + for prevent non-licensed pharmacist
    medical_stores_ids = models.JSONField(default=list)
    is_approved = models.BooleanField(default=False)

# NOTE =========================
'''
differnce:
- OneToOneField: one to one
- ForeginKey: many to one
----------------------------
'''