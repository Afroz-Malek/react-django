"""
StockstarAuthVersionOne Models
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import random
import string


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model with extended fields for StockstarCapital
    """
    
    # Basic Information
    email = models.EmailField(unique=True, db_index=True, max_length=255)
    user_name = models.CharField(max_length=100)
    user_middle_name = models.CharField(max_length=100, blank=True, null=True)
    user_surname = models.CharField(max_length=100)
    
    # Additional Information
    user_country_origin = models.CharField(max_length=100)
    user_contact_number = models.CharField(max_length=20)
    
    # Status Fields
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name', 'user_surname', 'user_country_origin', 'user_contact_number']
    
    class Meta:
        db_table = 'stockstarauthversionone_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return full name of user"""
        if self.user_middle_name:
            return f"{self.user_name} {self.user_middle_name} {self.user_surname}"
        return f"{self.user_name} {self.user_surname}"
    
    def get_short_name(self):
        """Return short name of user"""
        return self.user_name


class OTPVerification(models.Model):
    """
    Model to store OTP for email verification and password reset
    
    Updated: Now supports both signup verification and password reset
    """
    
    VERIFICATION_TYPE_CHOICES = [
        ('signup', 'Signup Verification'),
        ('password_reset', 'Password Reset'),  # NEW: Added password reset type
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_verifications'
    )
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    verification_type = models.CharField(
        max_length=20,
        choices=VERIFICATION_TYPE_CHOICES,
        default='signup'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # NEW: Additional tracking fields for password reset
    used_at = models.DateTimeField(null=True, blank=True)  # When OTP was used
    
    class Meta:
        db_table = 'stockstarauthversionone_otp_verifications'
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp_code', 'is_used']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'verification_type', 'is_used']),  # NEW: Added for faster queries
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.verification_type} - {self.otp_code}"
    
    @staticmethod
    def generate_otp(length=6):
        """Generate random OTP code"""
        return ''.join(random.choices(string.digits, k=length))
    
    def is_valid(self):
        """Check if OTP is still valid and not used"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used with timestamp"""
        self.is_used = True
        self.used_at = timezone.now()  # NEW: Track when it was used
        self.save(update_fields=['is_used', 'used_at'])
    
    def save(self, *args, **kwargs):
        """Override save to set expiry time"""
        if not self.pk:  # Only on creation
            from django.conf import settings
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            self.expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        super().save(*args, **kwargs)


class LoginAttempt(models.Model):
    """
    Model to track login attempts for security monitoring
    """
    
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'stockstarauthversionone_login_attempts'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['email', 'attempted_at']),
            models.Index(fields=['ip_address', 'attempted_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.email} - {status} at {self.attempted_at}"


class PasswordResetLog(models.Model):
    """
    NEW MODEL: Track password reset attempts for security audit
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_logs'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'stockstarauthversionone_password_reset_logs'
        verbose_name = 'Password Reset Log'
        verbose_name_plural = 'Password Reset Logs'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', 'requested_at']),
            models.Index(fields=['success', 'requested_at']),
        ]
    
    def __str__(self):
        status = "Completed" if self.success else "Pending"
        return f"Password Reset - {self.user.email} - {status} at {self.requested_at}"