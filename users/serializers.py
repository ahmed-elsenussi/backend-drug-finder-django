from rest_framework import serializers
from .models import User, Client, Pharmacist

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
        data = super().validate(attrs)

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

    # [SENU] mirror the name from the user table
    name = serializers.CharField(source='user.name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    id = serializers.IntegerField(source='user.id', read_only=True)  # [SENU]: NEED IT TO UPDATE PROFILE

    class Meta:
        model = Pharmacist
        fields = '__all__'


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
