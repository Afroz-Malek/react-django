from django.db import models
from django.conf import settings

class FyersToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='fyers_tokens'
    )
    client_id = models.CharField(max_length=255)
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fyers_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.client_id}"


class FyersProfile(models.Model):
    token = models.OneToOneField(
        FyersToken, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    fy_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)
    email_verified = models.CharField(max_length=1, default='N')
    mobile = models.CharField(max_length=20, null=True, blank=True)
    mobile_verified = models.CharField(max_length=1, default='N')
    pan = models.CharField(max_length=20, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    pin_created = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fyers_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.fy_id} - {self.name}"