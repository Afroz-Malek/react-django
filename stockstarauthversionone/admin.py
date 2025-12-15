"""
Django Admin Configuration for StockstarAuthVersionOne
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPVerification, LoginAttempt


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = [
        'email', 'user_name', 'user_surname', 
        'is_verified', 'is_active', 'is_staff', 'date_joined'
    ]
    list_filter = ['is_verified', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'user_name', 'user_surname', 'user_contact_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'user_name', 'user_middle_name', 'user_surname',
                'user_country_origin', 'user_contact_number'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'user_name', 'user_surname',
                'user_country_origin', 'user_contact_number',
                'password1', 'password2', 'is_staff', 'is_active'
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """OTP Verification Admin"""
    
    list_display = [
        'user', 'otp_code', 'verification_type',
        'is_used', 'created_at', 'expires_at'
    ]
    list_filter = ['verification_type', 'is_used', 'created_at']
    search_fields = ['user__email', 'otp_code']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'expires_at']
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('user', 'otp_code', 'verification_type')
        }),
        ('Status', {
            'fields': ('is_used', 'ip_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        }),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Login Attempt Admin"""
    
    list_display = [
        'email', 'success', 'ip_address',
        'attempted_at', 'failure_reason'
    ]
    list_filter = ['success', 'attempted_at']
    search_fields = ['email', 'ip_address']
    ordering = ['-attempted_at']
    readonly_fields = ['attempted_at']
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('email', 'ip_address', 'user_agent')
        }),
        ('Result', {
            'fields': ('success', 'failure_reason')
        }),
        ('Timestamp', {
            'fields': ('attempted_at',)
        }),
    )