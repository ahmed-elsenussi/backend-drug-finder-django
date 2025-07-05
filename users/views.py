from rest_framework import viewsets
from .models import User, Client, Pharmacist
from .serializers import UserSerializers, ClientSerializers, PharmacistSerializers, CurrentUserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission  # NEW: Added BasePermission
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

# [AMS] notification utilis ####
from notifications.utils import send_notification

#############################################

from .serializers import PharmacistSerializers

# [SENU]
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PharmacistFilter

# NEW PERMISSION FOR ADMIN-ONLY ACCESS
class IsAdmin(BasePermission):
    """
    Allow only admin users (is_staff or role='admin') to access the endpoint.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or request.user.role == 'admin')

# NEW ENDPOINT FOR ALL PHARMACISTS (ADMIN-ONLY)
@api_view(['GET'])
@permission_classes([IsAdmin])
def get_all_pharmacists(request):
    """
    Endpoint for admins to retrieve all pharmacists without pagination or filters.
    """
    pharmacists = Pharmacist.objects.select_related('user').filter(user__role='pharmacist')
    serializer = PharmacistSerializers(pharmacists, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

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
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        try:
            client = Client.objects.get(user=request.user)
            serializer = ClientSerializers(client, context={'request': request})

            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({'error': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            client = Client.objects.get(user=request.user)
            serializer = ClientSerializers(client, data=request.data, partial=True, context={'request': request})
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
    # [AMS]
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Check for license status change
        old_license_status = instance.license_status
        new_license_status = request.data.get('license_status')
        
        # Perform the update
        self.perform_update(serializer)
        
        # Handle notifications after successful update
        if old_license_status != new_license_status:
            self.handle_license_status_notification(instance, new_license_status, request.data.get('rejection_reason'))
        
        return Response(serializer.data)

    def handle_license_status_notification(self, pharmacist, new_status, rejection_reason=None):
        user = pharmacist.user
        if new_status == 'approved':
            send_notification(
                user=user,
                message="Your pharmacy license has been approved!",
                notification_type='message',
                send_email=True,
                email_subject="License Approved",
                email_template='emails/license_approved.html',
                email_context={
                    'user': user,
                    'pharmacist': pharmacist
                }
            )
        elif new_status == 'rejected':
            send_notification(
                user=user,
                message="Your pharmacy license application was rejected",
                notification_type='alert',
                send_email=True,
                email_subject="License Application Update",
                email_template='emails/license_rejected.html',
                email_context={
                    'user': user,
                    'pharmacist': pharmacist,
                    'reason': rejection_reason or "Not specified"
                }
            )

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

# [SENU]: HANDLE THE ERROR LOGIC OF NOT ADDING THE IMAGE IN THE PARENT USER TABLE
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_current_user_profile(request):
    user = request.user

    if request.method == 'GET':
        serializer = CurrentUserSerializer(user, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = UserSerializers(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)