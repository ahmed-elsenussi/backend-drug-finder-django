from rest_framework import serializers
from .models import User, Client, Pharmacist
from medical_stores.models import MedicalStore
from medical_stores.serializers import MedicalStoreSerializer

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# ======================== USER SERIALIZER ========================
class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'email_verified',
            'is_active',
            'is_staff',
            'role',
            'password'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        print(user.email_verification_token)

        # [AMS] Generate email verification token
        user.email_verification_token = str(uuid.uuid4())
        print(user.email_verification_token)

        user.email_verified = False
        user.is_active = False
        user.save()

        # [AMS] Send verification email
        verification_link = f"http://localhost:8000/users/verify-email/{user.email_verification_token}/"
        html_content = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_link': verification_link,
        })

        # Render plain text content
        text_content = strip_tags(render_to_string('emails/email_verification.txt', {
            'user': user,
            'verification_link': verification_link,
        }))

        # Create and send email
        email = EmailMultiAlternatives(
            'Verify your email',
            text_content,
            settings.EMAIL_HOST_USER,
            [user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return user
# =================== TOKEN LOGIN SERIALIZER ======================
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except serializers.ValidationError as e:
            # Handle Google users who haven't set password
            if "No active account found" in str(e):
                user = User.objects.get(email=attrs.get('email'))
                if user.has_usable_password():
                    raise e
                else:
                    raise serializers.ValidationError(
                        "Your account was created with Google. Please use Google login."
                    )
            else:
                raise e
        # Check if email is verified
        if not self.user.email_verified:
            raise serializers.ValidationError("Email not verified. Please check your email for verification link.")

        # Base data for all roles
        user_data = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
            'role': self.user.role,
        }

        # Add pharmacist.has_store if the role is pharmacist
        if self.user.role == 'pharmacist' and hasattr(self.user, 'pharmacist'):
            user_data['pharmacist'] = {
                'has_store': self.user.pharmacist.has_store
            }

        data['user'] = user_data  
        return data



# ===================== CLIENT SERIALIZER =========================
class ClientSerializers(serializers.ModelSerializer):

    # mirror the name from the user table
    name = serializers.CharField(source='user.name', read_only= True)
    user_id = serializers.IntegerField(source='user.id', read_only = True)
    email = serializers.EmailField(source='user.email', read_only=True)


    class Meta:
        model = Client
        fields = '__all__'


# =================== PHARMACIST SERIALIZER =======================
class PharmacistSerializers(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    id = serializers.IntegerField(source='user.id', read_only=True)
    medical_stores_data = serializers.SerializerMethodField()

    class Meta:
        model = Pharmacist
        fields = [
            'id',
            'user_id',
            'name',
            'image_profile',
            'image_license',
            'license_status',
            'has_store',
            'medical_stores_ids',
            'medical_stores_data',
        ]
        extra_kwargs = {
            'image_license': {'required': False}  # Make field optional for updates
        }

    def update(self, instance, validated_data):
        # Handle file fields separately
        if 'image_license' in self.context['request'].FILES:
            instance.image_license = validated_data.get('image_license', instance.image_license)
        instance.license_status = validated_data.get('license_status', instance.license_status)
        instance.save()
        return instance


    def get_medical_stores_data(self, obj):
        from medical_stores.models import MedicalStore
        from medical_stores.serializers import MedicalStoreSerializer

        if obj.has_store and obj.medical_stores_ids:
            # Ensure medical_stores_ids is a list
            store_ids = obj.medical_stores_ids
            if isinstance(store_ids, int):
                store_ids = [store_ids]  # wrap single int in a list

            stores = MedicalStore.objects.filter(id__in=store_ids)
            if stores.exists():
                return MedicalStoreSerializer(stores.first()).data 
        return None

    








# =========== GET USER PROFILE WITH IMAGE HANDLING ================
# [SENU]: HANDLE THE ERROR LOGIC OF NOT ADDING THE IMAGE IN THE PARENT USER TABLE
class CurrentUserSerializer(serializers.ModelSerializer):
    image_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'role', 'image_profile']

    def get_image_profile(self, user):
        request = self.context.get('request')
        if user.role == 'client' and hasattr(user, 'client'):
            return request.build_absolute_uri(user.client.image_profile.url) if user.client.image_profile else None
        if user.role == 'pharmacist' and hasattr(user, 'pharmacist'):
            return request.build_absolute_uri(user.pharmacist.image_profile.url) if user.pharmacist.image_profile else None
        return None  # admin has no image
