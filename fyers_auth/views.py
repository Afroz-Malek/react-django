import hashlib
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decouple import config
from .serializers import GenerateTokenSerializer, FyersTokenSerializer, FyersProfileSerializer
from .models import FyersToken, FyersProfile


class GenerateAccessTokenView(APIView):
    """
    Generate Fyers Access Token using auth code and fetch profile
    """
    
    def post(self, request):
        try:
            serializer = GenerateTokenSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Invalid input data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            client_id = serializer.validated_data['clientId']
            secret_key = serializer.validated_data['secretKey']
            auth_code = serializer.validated_data['authCode']
            
            # Step 1: Generate app_id_hash (SHA256 of clientId:secretKey)
            app_id_hash = hashlib.sha256(
                f"{client_id}:{secret_key}".encode()
            ).hexdigest()
            
            print(f"Generated app_id_hash: {app_id_hash}")
            
            # Step 2: Call Fyers API to validate auth code
            fyers_url = "https://api-t1.fyers.in/api/v3/validate-authcode"
            
            payload = {
                "grant_type": "authorization_code",
                "appIdHash": app_id_hash,
                "code": auth_code
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            fyers_response = requests.post(fyers_url, json=payload, headers=headers)
            fyers_data = fyers_response.json()
            
            print(f"Fyers API Response: {fyers_data}")
            
            # Step 3: Check response
            if fyers_data.get('s') == 'ok' and fyers_data.get('code') == 200:
                access_token = fyers_data.get('access_token')
                refresh_token = fyers_data.get('refresh_token')
                
                # Step 4: Fetch user profile using access token
                # IMPORTANT: Fyers requires the full access token with client_id prefix
                profile_url = "https://api-t1.fyers.in/api/v3/profile"
                profile_headers = {
                    "Authorization": f"{client_id}:{access_token}"
                }
                
                profile_response = requests.get(profile_url, headers=profile_headers)
                profile_data = profile_response.json()
                
                print(f"Profile API Response: {profile_data}")
                
                profile_info = None
                if profile_data.get('s') == 'ok' and profile_data.get('code') == 200:
                    profile_info = profile_data.get('data')
                
                return Response({
                    'success': True,
                    'message': 'Access token generated successfully',
                    'data': {
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'profile': profile_info
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': fyers_data.get('message', 'Failed to generate access token'),
                    'error': fyers_data
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except requests.exceptions.RequestException as e:
            return Response({
                'success': False,
                'message': 'Error connecting to Fyers API',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetProfileView(APIView):
    """
    Get Fyers profile using access token
    """
    
    def post(self, request):
        try:
            access_token = request.data.get('accessToken')
            client_id = request.data.get('clientId')
            
            if not access_token:
                return Response({
                    'success': False,
                    'message': 'Access token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not client_id:
                return Response({
                    'success': False,
                    'message': 'Client ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Call Fyers API to get profile
            profile_url = "https://api-t1.fyers.in/api/v3/profile"
            headers = {
                "Authorization": f"{client_id}:{access_token}"
            }
            
            profile_response = requests.get(profile_url, headers=headers)
            profile_data = profile_response.json()
            
            if profile_data.get('s') == 'ok' and profile_data.get('code') == 200:
                return Response({
                    'success': True,
                    'message': 'Profile fetched successfully',
                    'data': profile_data.get('data')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to fetch profile',
                    'error': profile_data
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error fetching profile',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyTokenView(APIView):
    """
    Verify if Fyers access token is valid
    """
    
    def post(self, request):
        try:
            access_token = request.data.get('accessToken')
            client_id = request.data.get('clientId')
            
            if not access_token:
                return Response({
                    'success': False,
                    'message': 'Access token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not client_id:
                return Response({
                    'success': False,
                    'message': 'Client ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Call Fyers API to verify token
            fyers_url = "https://api-t1.fyers.in/api/v3/profile"
            
            headers = {
                "Authorization": f"{client_id}:{access_token}"
            }
            
            fyers_response = requests.get(fyers_url, headers=headers)
            fyers_data = fyers_response.json()
            
            if fyers_data.get('s') == 'ok' and fyers_data.get('code') == 200:
                return Response({
                    'success': True,
                    'message': 'Token is valid',
                    'data': fyers_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid or expired token',
                    'error': fyers_data
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error verifying token',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserTokensView(APIView):
    """
    Get all active tokens for current user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            tokens = FyersToken.objects.filter(
                user=request.user,
                is_active=True
            )
            serializer = FyersTokenSerializer(tokens, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error fetching tokens',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)