from rest_framework import serializers
from .models import FyersToken, FyersProfile

class GenerateTokenSerializer(serializers.Serializer):
    clientId = serializers.CharField(max_length=255, required=True)
    secretKey = serializers.CharField(max_length=255, required=True)
    authCode = serializers.CharField(required=True)
    state = serializers.CharField(required=False)


class FyersProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FyersProfile
        fields = [
            'id', 'fy_id', 'name', 'email', 'email_verified',
            'mobile', 'mobile_verified', 'pan', 'display_name',
            'pin_created', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FyersTokenSerializer(serializers.ModelSerializer):
    profile = FyersProfileSerializer(read_only=True)
    
    class Meta:
        model = FyersToken
        fields = ['id', 'client_id', 'access_token', 'created_at', 'is_active', 'profile']
        read_only_fields = ['id', 'created_at']