"""
Authentication Views - StockstarCapital User Creation Version One

This module contains all authentication-related views including:
1. User Registration (register_user)
2. OTP Verification (verify_otp)
3. OTP Resend (resend_otp)
4. User Login (login_user)
5. User Logout (logout_user)
6. Forgot Password (forgot_password)
7. Verify Reset OTP (verify_reset_otp)
8. Reset Password (reset_password)
9. Get User Details (get_user_details) - with cache prevention

IMPORTANT: Cache prevention is applied to all sensitive views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from stockstarauthversionone.models import User, OTPVerification, LoginAttempt
from stockstarauthversionone.serializers import (
    UserCreationSerializer,
    OTPVerificationSerializer,
    ResendOTPSerializer,
    UserLoginSerializer,
    UserSerializer,
    ForgotPasswordRequestSerializer,
    VerifyResetOTPSerializer,
    ResetPasswordSerializer
)
from stockstarauthversionone.utils import get_client_ip, get_user_agent
from stockstarauthversionone.tasks import (
    initialize_ray,
    send_otp_email_async,
    send_welcome_email_async,
    send_password_reset_otp_email_async
)

import logging

logger = logging.getLogger(__name__)

# Initialize Ray on module load
initialize_ray()


class StockstarCapitalUserCreationVersionOne(APIView):
    """
    Main Authentication API Class for StockstarCapital
    Version: 1.0
    
    This class handles all user authentication operations:
    - User registration with email OTP verification
    - OTP verification
    - OTP resend functionality
    - User login
    - User logout
    - Forgot password flow
    - Password reset
    
    All endpoints follow the naming convention:
    /api/authentication/stockstarcapital-usercreation-versionone/<action>/
    """
    
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        """
        Route POST requests to appropriate handler based on action
        """
        action = kwargs.get('action', '')
        
        if action == 'register':
            return self.register_user(request)
        elif action == 'verify-otp':
            return self.verify_otp(request)
        elif action == 'resend-otp':
            return self.resend_otp(request)
        elif action == 'login':
            return self.login_user(request)
        elif action == 'logout':
            return self.logout_user(request)
        elif action == 'forgot-password':
            return self.forgot_password(request)
        elif action == 'verify-reset-otp':
            return self.verify_reset_otp(request)
        elif action == 'reset-password':
            return self.reset_password(request)
        else:
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid action specified'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # ==========================================
    # Function 1: register_user
    # ==========================================
    def register_user(self, request):
        """
        Register a new user and send OTP verification email
        
        Expected Request Body:
        {
            "email": "user@example.com",
            "user_name": "John",
            "user_middle_name": "Michael",
            "user_surname": "Doe",
            "user_country_origin": "United States",
            "user_contact_number": "+1234567890",
            "password": "SecurePass123!",
            "password_confirmation": "SecurePass123!"
        }
        """
        try:
            serializer = UserCreationSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                user = serializer.save()
                otp_code = OTPVerification.generate_otp(length=settings.OTP_LENGTH)
                
                otp_verification = OTPVerification.objects.create(
                    user=user,
                    otp_code=otp_code,
                    verification_type='signup',
                    ip_address=get_client_ip(request)
                )
                
                email_sent = send_otp_email_async(
                    recipient_email=user.email,
                    otp_code=otp_code,
                    user_name=user.user_name
                )
                
                if not email_sent:
                    transaction.set_rollback(True)
                    return Response(
                        {
                            'status': 'error',
                            'message': 'Failed to send OTP email. Please try again.'
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                logger.info(f"User registered successfully: {user.email}")
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'User registered successfully. OTP sent to your email.',
                        'data': {
                            'user_id': user.id,
                            'email': user.email,
                            'full_name': user.get_full_name(),
                            'otp_expires_in': f'{settings.OTP_EXPIRY_MINUTES} minutes'
                        }
                    },
                    status=status.HTTP_201_CREATED
                )
        
        except Exception as e:
            logger.error(f"Error in register_user: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred during registration. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 2: verify_otp
    # ==========================================
    def verify_otp(self, request):
        """
        Verify OTP code sent to user's email
        
        Expected Request Body:
        {
            "email": "user@example.com",
            "otp_code": "123456"
        }
        """
        try:
            serializer = OTPVerificationSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                user = User.objects.get(email=email.lower())
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'User not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if user.is_verified:
                return Response(
                    {
                        'status': 'error',
                        'message': 'User is already verified'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                otp_verification = OTPVerification.objects.filter(
                    user=user,
                    verification_type='signup',
                    is_used=False
                ).latest('created_at')
            except OTPVerification.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'No valid OTP found. Please request a new OTP.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if otp_verification.otp_code != otp_code:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid OTP code'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not otp_verification.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'OTP has expired. Please request a new OTP.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                otp_verification.mark_as_used()
                user.is_verified = True
                user.is_active = True
                user.save(update_fields=['is_verified', 'is_active'])
                
                send_welcome_email_async(user.email, user.user_name)
                
                logger.info(f"User verified successfully: {user.email}")
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Email verified successfully. You can now login.',
                        'data': {
                            'user_id': user.id,
                            'email': user.email,
                            'is_verified': user.is_verified
                        }
                    },
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            logger.error(f"Error in verify_otp: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred during verification. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 3: resend_otp
    # ==========================================
    def resend_otp(self, request):
        """
        Resend OTP to user's email
        
        Expected Request Body:
        {
            "email": "user@example.com"
        }
        """
        try:
            serializer = ResendOTPSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email.lower())
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'User not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if user.is_verified:
                return Response(
                    {
                        'status': 'error',
                        'message': 'User is already verified'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            otp_code = OTPVerification.generate_otp(length=settings.OTP_LENGTH)
            
            with transaction.atomic():
                OTPVerification.objects.filter(
                    user=user,
                    verification_type='signup',
                    is_used=False
                ).update(is_used=True)
                
                otp_verification = OTPVerification.objects.create(
                    user=user,
                    otp_code=otp_code,
                    verification_type='signup',
                    ip_address=get_client_ip(request)
                )
                
                email_sent = send_otp_email_async(
                    recipient_email=user.email,
                    otp_code=otp_code,
                    user_name=user.user_name
                )
                
                if not email_sent:
                    return Response(
                        {
                            'status': 'error',
                            'message': 'Failed to send OTP email. Please try again.'
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                logger.info(f"OTP resent successfully to: {user.email}")
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'New OTP sent to your email.',
                        'data': {
                            'email': user.email,
                            'otp_expires_in': f'{settings.OTP_EXPIRY_MINUTES} minutes'
                        }
                    },
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            logger.error(f"Error in resend_otp: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 4: login_user
    # ==========================================
    def login_user(self, request):
        """
        Login user with email and password
        
        Expected Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
        """
        try:
            serializer = UserLoginSerializer(data=request.data)
            
            if not serializer.is_valid():
                email = request.data.get('email', 'unknown')
                LoginAttempt.objects.create(
                    email=email,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    success=False,
                    failure_reason='Validation failed'
                )
                
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = serializer.validated_data['user']
            
            login(request, user)
            
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            LoginAttempt.objects.create(
                email=user.email,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
            
            user_data = UserSerializer(user).data
            
            logger.info(f"User logged in successfully: {user.email}")
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Login successful',
                    'data': {
                        'user': user_data,
                        'session_id': request.session.session_key
                    }
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error in login_user: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred during login. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 5: logout_user
    # ==========================================
    def logout_user(self, request):
        """
        Logout current user
        """
        try:
            if request.user.is_authenticated:
                user_email = request.user.email
                logout(request)
                logger.info(f"User logged out successfully: {user_email}")
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Logout successful'
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'status': 'error',
                        'message': 'No active session found'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error in logout_user: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred during logout'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 6: forgot_password
    # ==========================================
    def forgot_password(self, request):
        """
        Initiate password reset by sending OTP to user's email
        
        Expected Request Body:
        {
            "email": "user@example.com"
        }
        """
        try:
            serializer = ForgotPasswordRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # For security, return success even if user doesn't exist
                # This prevents email enumeration attacks
                return Response(
                    {
                        'status': 'success',
                        'message': 'If an account exists with this email, a password reset OTP has been sent.',
                        'data': {
                            'email': email,
                            'otp_expires_in': f'{settings.OTP_EXPIRY_MINUTES} minutes'
                        }
                    },
                    status=status.HTTP_200_OK
                )
            
            # Check if user is verified
            if not user.is_verified:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Please verify your email before resetting password.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate OTP
            otp_code = OTPVerification.generate_otp(length=settings.OTP_LENGTH)
            
            with transaction.atomic():
                # Mark all previous password reset OTPs as used
                OTPVerification.objects.filter(
                    user=user,
                    verification_type='password_reset',
                    is_used=False
                ).update(is_used=True)
                
                # Create new OTP verification
                otp_verification = OTPVerification.objects.create(
                    user=user,
                    otp_code=otp_code,
                    verification_type='password_reset',
                    ip_address=get_client_ip(request)
                )
                
                # Send OTP email
                email_sent = send_password_reset_otp_email_async(
                    recipient_email=user.email,
                    otp_code=otp_code,
                    user_name=user.user_name
                )
                
                if not email_sent:
                    return Response(
                        {
                            'status': 'error',
                            'message': 'Failed to send OTP email. Please try again.'
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                logger.info(f"Password reset OTP sent to: {user.email}")
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Password reset OTP has been sent to your email.',
                        'data': {
                            'email': user.email,
                            'otp_expires_in': f'{settings.OTP_EXPIRY_MINUTES} minutes'
                        }
                    },
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            logger.error(f"Error in forgot_password: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 7: verify_reset_otp
    # ==========================================
    def verify_reset_otp(self, request):
        """
        Verify password reset OTP code
        
        Expected Request Body:
        {
            "email": "user@example.com",
            "otp_code": "123456"
        }
        """
        try:
            serializer = VerifyResetOTPSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'User not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get latest unused password reset OTP
            try:
                otp_verification = OTPVerification.objects.filter(
                    user=user,
                    verification_type='password_reset',
                    is_used=False
                ).latest('created_at')
            except OTPVerification.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'No valid OTP found. Please request a new OTP.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify OTP code
            if otp_verification.otp_code != otp_code:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid OTP code'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OTP is expired
            if not otp_verification.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'OTP has expired. Please request a new OTP.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Password reset OTP verified for: {user.email}")
            
            return Response(
                {
                    'status': 'success',
                    'message': 'OTP verified successfully. You can now reset your password.',
                    'data': {
                        'email': user.email,
                        'otp_verified': True
                    }
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error in verify_reset_otp: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==========================================
    # Function 8: reset_password
    # ==========================================
    def reset_password(self, request):
        """
        Reset user password after OTP verification
        
        Expected Request Body:
        {
            "email": "user@example.com",
            "otp_code": "123456",
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        }
        """
        try:
            serializer = ResetPasswordSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'User not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get latest unused password reset OTP
            try:
                otp_verification = OTPVerification.objects.filter(
                    user=user,
                    verification_type='password_reset',
                    is_used=False
                ).latest('created_at')
            except OTPVerification.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'No valid OTP found. Please request a new OTP.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify OTP code
            if otp_verification.otp_code != otp_code:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid OTP code'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OTP is expired
            if not otp_verification.is_valid():
                return Response(
                    {
                        'status': 'error',
                        'message': 'OTP has expired. Please request a new OTP.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Mark OTP as used
                otp_verification.mark_as_used()
                
                # Update password
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                logger.info(f"Password reset successfully for: {user.email}")
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Password reset successful. You can now login with your new password.',
                        'data': {
                            'email': user.email
                        }
                    },
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            logger.error(f"Error in reset_password: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==========================================
# Additional View: Get User Details
# WITH CACHE PREVENTION
# ==========================================
class StockstarCapitalUserDetailVersionOne(APIView):
    """
    Get User Details View
    
    This view returns detailed information about a specific user.
    Cache prevention is applied to prevent browsers from caching sensitive user data.
    
    Endpoint: /api/authentication/stockstarcapital-usercreation-versionone/user/<user_id>/
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(never_cache)
    def get(self, request, user_id=None, *args, **kwargs):
        """
        Get User Details by ID
        
        The @method_decorator(never_cache) ensures that browsers do NOT cache this response.
        This prevents the "back button" issue where users see cached data after logout.
        """
        try:
            # If no user_id provided, return current user
            if user_id is None:
                user = request.user
            else:
                # Check if user has permission to view other users
                if not request.user.is_staff and request.user.id != int(user_id):
                    return Response(
                        {
                            'status': 'error',
                            'message': 'You do not have permission to view this user'
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response(
                        {
                            'status': 'error',
                            'message': 'User not found'
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            user_data = UserSerializer(user).data
            
            return Response(
                {
                    'status': 'success',
                    'message': 'User details retrieved successfully',
                    'data': user_data
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error in get_user_details: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'An error occurred while retrieving user details'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )