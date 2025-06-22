from rest_framework import serializers
from .models import User, Client, Pharmacist

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# USER SERAILZIER
class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name',
                'email',
                'email_verified',
                'is_active',
                'is_staff',
                'role','password']
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
        
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        print(user.email_verification_token)
        #[AMS] Generate email verification token
        user.email_verification_token = str(uuid.uuid4())
        print(user.email_verification_token)
        user.email_verified = False
        user.is_active = False
        user.save()
        
        #[AMS] Send verification email
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
            
        # Add custom claims
        data.update({
            'email': self.user.email,
            'role': self.user.role,
            'name': self.user.name
        })
        return data

# CLIENT SERIALIZER
class ClientSerializers(serializers.ModelSerializer):

    # mirror the name from the user table
    name = serializers.CharField(source='user.name', read_only= True)
    user_id = serializers.IntegerField(source='user.id', read_only = True)
    email = serializers.EmailField(source='user.email', read_only=True)


    class Meta:
        model = Client
        fields = '__all__'
    

# PHARAMCIST SERIALIZER
class PharmacistSerializers(serializers.ModelSerializer):

    # mirror the name from the user table
    name = serializers.CharField(source='user.name', read_only= True)
    user_id = serializers.IntegerField(source='user.id', read_only = True)
    
    class Meta:
        model = Pharmacist
        fields = '__all__'