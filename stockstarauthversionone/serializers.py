"""
StockstarAuthVersionOne Serializers for Data Validation
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from stockstarauthversionone.models import User, OTPVerification
import re


class UserCreationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with all required fields
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters"
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm your password"
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'user_name',
            'user_middle_name',
            'user_surname',
            'user_country_origin',
            'user_contact_number',
            'password',
            'password_confirmation'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'user_name': {'required': True},
            'user_surname': {'required': True},
            'user_country_origin': {'required': True},
            'user_contact_number': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email format and uniqueness"""
        value = value.lower().strip()
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Enter a valid email address.")
        
        return value
    
    def validate_user_contact_number(self, value):
        """Validate contact number format"""
        cleaned_number = re.sub(r'[\s\-\(\)]', '', value)
        
        if not re.match(r'^\+?\d{10,15}$', cleaned_number):
            raise serializers.ValidationError(
                "Enter a valid contact number (10-15 digits, optional + prefix)"
            )
        return cleaned_number
    
    def validate_user_name(self, value):
        """Validate user name"""
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if not re.match(r'^[a-zA-Z\s\-\']+$', value):
            raise serializers.ValidationError("Name can only contain letters, spaces, hyphens, and apostrophes.")
        return value
    
    def validate_user_surname(self, value):
        """Validate user surname"""
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Surname must be at least 2 characters long.")
        if not re.match(r'^[a-zA-Z\s\-\']+$', value):
            raise serializers.ValidationError("Surname can only contain letters, spaces, hyphens, and apostrophes.")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation matches password"""
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({
                "password_confirmation": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user with validated data"""
        validated_data.pop('password_confirmation')
        user = User.objects.create_user(**validated_data)
        return user


class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification
    """
    
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="6-digit OTP code"
    )
    
    def validate_otp_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class ResendOTPSerializer(serializers.Serializer):
    """
    Serializer for resending OTP
    """
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that user exists"""
        value = value.lower().strip()
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()
    
    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found with this email address."})
        
        if not user.is_verified:
            raise serializers.ValidationError({"email": "Please verify your email address before logging in."})
        
        if not user.is_active:
            raise serializers.ValidationError({"email": "This account has been deactivated."})
        
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError({"password": "Incorrect password."})
        
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (for responses)
    """
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'user_name',
            'user_middle_name',
            'user_surname',
            'full_name',
            'user_country_origin',
            'user_contact_number',
            'is_verified',
            'date_joined',
        ]
        read_only_fields = ['id', 'is_verified', 'date_joined']
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()


# ==========================================
# Forgot Password Serializers
# ==========================================

class ForgotPasswordRequestSerializer(serializers.Serializer):
    """
    Serializer for forgot password request
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate email exists"""
        email = value.lower().strip()
        
        # Check if user exists
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("No account found with this email address.")
        
        return email


class VerifyResetOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying password reset OTP
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, min_length=6, max_length=6)
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()
    
    def validate_otp_code(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting password after OTP verification
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()
    
    def validate_otp_code(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value
    
    def validate(self, data):
        """Validate passwords match"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Password strength validation
        password = data['new_password']
        
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError({
                'new_password': 'Password must contain at least one uppercase letter.'
            })
        
        if not any(char.islower() for char in password):
            raise serializers.ValidationError({
                'new_password': 'Password must contain at least one lowercase letter.'
            })
        
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError({
                'new_password': 'Password must contain at least one digit.'
            })
        
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
            raise serializers.ValidationError({
                'new_password': 'Password must contain at least one special character.'
            })
        
        return data