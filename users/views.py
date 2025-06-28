from rest_framework import viewsets
from .models import User, Client, Pharmacist
from .serializers import UserSerializers, ClientSerializers, PharmacistSerializers, CurrentUserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from inventory.permissions import IsAdminOrReadOnly
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.views import APIView
from django.db import transaction  
from django.shortcuts import render
from users.permissions import IsSelfPharmacistOrAdmin
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser # NEW ADDED FOR HANDLING UPDATE LICENSE STATUS

# [AMS] GOOGLE AUTH #######################
from rest_framework.views import APIView
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
#############################################

from .serializers import PharmacistSerializers

# [SENU]
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PharmacistFilter

# USER VIEWSET
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializers
    
    def get_permissions(self):
        # [SARA]: Allow anyone to create (register), require auth for other actions
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrReadOnly()]
    
    def create(self, request, *args, **kwargs):
        #         ('guest', 'Guest'),('client', 'Client'),
        # ('pharmacist', 'Pharmacist'),('admin', 'Admin')
        print(request.data)
        with transaction.atomic(): 
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            role = request.data.get('role', 'client')
            if role == 'pharmacist':
                image_profile = request.FILES.get('image_profile')
                image_license = request.FILES.get('image_license')
                if not image_license :
                    user.delete()  # Rollback user creation
                    print ('no image_license')
                    return Response(
                        {
                            'error':'you must upload license Image'
                            },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if not image_profile:
                    image_profile=''
                
                # [SENU] Use get_or_create to prevent duplicate Doctor records
                pharmacist, created = Pharmacist.objects.get_or_create(
                    user=user,
                    defaults={
                        'image_license': image_license,
                        'image_profile': image_profile
                    }
                )
                if not created and (image_license or image_profile):
                    # Update images if provided
                    if image_license:
                        pharmacist.image_license = image_license
                    if image_profile:
                        pharmacist.image_profile = image_profile
                    pharmacist.save()
            
            elif role == 'client':
                image_profile = request.FILES.get('image_profile')
                if not image_profile:
                    image_profile=""
                Client.objects.create(
                    user=user,
                    image_profile=image_profile,
                )
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

# CLIENT VIEWSET
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializers
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

# get the client profile of the authenticated user
# and allow them to update it{amira}
class ClientViewprofile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client = Client.objects.get(user=request.user)
            serializer = ClientSerializers(client)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({'error': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            client = Client.objects.get(user=request.user)
            serializer = ClientSerializers(client, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({'error': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)



# PHARMACIST VIEWSET
class PharmacistViewSet(viewsets.ModelViewSet):
    queryset = Pharmacist.objects.all()
    serializer_class = PharmacistSerializers
    permission_classes = [IsAuthenticated, IsSelfPharmacistOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PharmacistFilter
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # NEW ADDED FOR HANDLING UPDATE LICENSE STATUS
    

#[AMS] 📩 Email Verification
@api_view(['GET'])
def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        user.email_verified = True
        
        user.email_verification_token = None
        user.is_active = True
        user.save()
        return render(request, 'accounts/email_confirmed.html')
    except User.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

# [AMS] Login 
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # First check if user exists and is_active status
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Check if email is verified (which would make is_active=True)
            if not user.email_verified:
                return Response({
                    'error': 'email_not_verified',
                    'detail': 'Please verify your email before logging in',
                    'email': user.email
                }, status=status.HTTP_403_FORBIDDEN)
                
            # Check if account is active (should be true if email verified)
            if not user.is_active:
                return Response({
                    'error': 'account_inactive',
                    'message': 'Account is not active'
                }, status=status.HTTP_403_FORBIDDEN)
                
        except User.DoesNotExist:
            # Don't reveal whether user exists for security
            pass

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            try:
                # Decode the access token to get user ID
                access_token = AccessToken(response.data['access'])
                user_id = access_token['user_id']

                # Get the user object
                user = User.objects.get(id=user_id)

                # [SENU] Add user data to the response
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,  
                    'role': user.role,  # make sure your User model has this field
                }

                # [SENU] Include pharmacist.has_store if role is pharmacist
                if user.role == 'pharmacist' and hasattr(user, 'pharmacist'):
                    user_data['pharmacist'] = {
                        'has_store': user.pharmacist.has_store
                    }

                response.data['user'] = user_data

            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return response

# [AMS] GOOGLE AUTHENTICATION (LOGIN)
class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get('token')
        
        try:
            # Verify Google token
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # Get user email from Google payload
            email = idinfo['email']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user if doesn't exist
                user = User.objects.create(
                    email=email,
                    name=idinfo.get('name', ''),
                    role='client',  # Default role
                    email_verified=True,
                    is_active=True
                )
                user.set_unusable_password()  # No password needed
                user.save()
                
                # Create client profile
                Client.objects.create(user=user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Prepare response
            response_data = {
                'access': str(access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                }
            }
            
            # Add pharmacist data if applicable
            if user.role == 'pharmacist' and hasattr(user, 'pharmacist'):
                response_data['user']['pharmacist'] = {
                    'has_store': user.pharmacist.has_store
                }
            
            return Response(response_data)
            
        except ValueError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
###################################
# [SENU]: getting the current user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_user(request):
    user = request.user
    return Response({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role
    })


# [SENU]: get the pharmacist dat
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_pharmacist(request):
    try:
        pharmacist = Pharmacist.objects.get(user=request.user)
        serializer = PharmacistSerializers(pharmacist)
        return Response(serializer.data)
    except Pharmacist.DoesNotExist:
        return Response({'error': 'Pharmacist profile not found'}, status=404)


# ============================================

# [SENU]: HANDLE THE ERROR LOGIC OF NOT ADDING THE IMAGE IN THE PARENT USER TABLE
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user_profile(request):
    serializer = CurrentUserSerializer(request.user, context={'request': request})
    return Response(serializer.data)





#====================================
# from config import settings
# import uuid
# from django.core.mail import send_mail
# from rest_framework import status
# import logging
# from django.utils import timezone
# from datetime import timedelta
# from django.core.exceptions import ValidationError
# from django.contrib.auth.password_validation import validate_password
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.core.mail import EmailMultiAlternatives

# def send_password_reset_email(email, context):
#     """Helper function to send password reset email"""
#     html_message = render_to_string('emails/password_reset.html', context)
#     plain_message = strip_tags(render_to_string('emails/password_reset.txt', context))
    
#     email = EmailMultiAlternatives(
#         subject=f"{context['site_name']} - Password Reset",
#         body=plain_message,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to=[email],
#         reply_to=[context['support_email']]
#     )
#     email.attach_alternative(html_message, "text/html")
#     email.send()

# logger = logging.getLogger(__name__)

# @api_view(['POST'])
# def forget_password (request):
#     email = request.data.get('email')
#     if not email:
#         return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         user = User.objects.get(email=email)
#         if not user.is_active:
#             logger.warning(f"Inactive user attempted password reset: {email}")
#             return Response(
#                 {'error': 'Account is not active. Please contact support.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Generate token with expiration (24 hours)
#         user.email_verification_token = str(uuid.uuid4())
#         user.save()

#         # Construct reset link
#         reset_url = f"http://localhost:8000/reset-password/{user.email_verification_token}/"
        
#         # HTML email with template
#         context = {
#             'user': user,
#             'reset_url': reset_url,
#             'support_email': settings.SUPPORT_EMAIL,
#             'site_name': settings.SITE_NAME
#         }

#         try:
#             send_password_reset_email(user.email, context)
#             logger.info(f"Password reset email sent to {email}")
#             return Response(
#                 {'message': 'Password reset link has been sent to your email'},
#                 status=status.HTTP_200_OK
#             )
#         except Exception as e:
#             logger.error(f"Email sending failed to {email}: {str(e)}")
#             return Response(
#                 {'error': 'Failed to send reset email. Please try again later.'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#     except User.DoesNotExist:
#         # Generic response for security
#         logger.info(f"Password reset attempt for non-existent email: {email}")
#         return Response(
#             {'message': 'If this email exists in our system, you will receive a reset link'},
#             status=status.HTTP_200_OK
#         )

            
# def validate_reset_password (request, token):        
#     try:
#         user = User.objects.get(email_verification_token=token)
#         if user.is_active:
#             new_password = request.data['new_password']
#             confirm_password = request.data['confirm_password']
#             user.set_password(new_password)
#             user.email_verification_token = None
#             user.save()
#             return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
#         else:
#             return Response({'error': 'User is not active'}, status=status.HTTP_400_BAD_REQUEST)
#     except User.DoesNotExist:
        
#         return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


