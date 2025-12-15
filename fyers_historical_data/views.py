"""
FYERS Historical Data Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Exchange, Instrument, Symbol, HistoricalDataRequest
from .serializers import (
    ExchangeSerializer,
    InstrumentSerializer,
    SymbolSerializer,
    HistoricalDataRequestSerializer,
    HistoricalDataRequestCreateSerializer
)

import logging

logger = logging.getLogger(__name__)


class ExchangeListView(APIView):
    """
    Get list of all exchanges
    """
    # Temporarily disable authentication for testing
    permission_classes = []
    
    def get(self, request):
        """Get all exchanges"""
        try:
            exchanges = Exchange.objects.using('fyers').all()
            serializer = ExchangeSerializer(exchanges, many=True)
            
            return Response({
                'status': 'success',
                'message': 'Exchanges retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching exchanges: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch exchanges',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstrumentListView(APIView):
    """
    Get list of all instruments
    """
    permission_classes = []
    
    def get(self, request):
        """Get all instruments"""
        try:
            instruments = Instrument.objects.using('fyers').all()
            serializer = InstrumentSerializer(instruments, many=True)
            
            return Response({
                'status': 'success',
                'message': 'Instruments retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching instruments: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch instruments',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SymbolListView(APIView):
    """
    Get list of symbols filtered by exchange and instrument
    """
    permission_classes = []
    
    def get(self, request):
        """Get symbols filtered by exchange and instrument"""
        try:
            exchange_id = request.query_params.get('exchange')
            instrument_id = request.query_params.get('instrument')
            search = request.query_params.get('search', '')
            
            if not exchange_id or not instrument_id:
                return Response({
                    'status': 'error',
                    'message': 'Exchange and instrument parameters are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Filter symbols
            symbols = Symbol.objects.using('fyers').filter(
                exchange_id=exchange_id,
                instrument_id=instrument_id,
                is_active=True
            )
            
            # Apply search if provided
            if search:
                symbols = symbols.filter(
                    Q(symbol_code__icontains=search) |
                    Q(symbol_name__icontains=search)
                )
            
            # Limit results
            symbols = symbols[:100]
            
            serializer = SymbolSerializer(symbols, many=True)
            
            return Response({
                'status': 'success',
                'message': f'{symbols.count()} symbols found',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error fetching symbols: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch symbols',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistoricalDataRequestView(APIView):
    """
    Submit historical data fetch request
    """
    permission_classes = []
    
    def post(self, request):
        """Submit fetch request"""
        try:
            serializer = HistoricalDataRequestCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create request
            data = serializer.validated_data
            
            # For testing, use a dummy email if user is not authenticated
            user_email = request.user.email if request.user.is_authenticated else 'test@example.com'
            
            historical_request = HistoricalDataRequest.objects.using('fyers').create(
                user_email=user_email,
                exchange_id=data['exchange_id'],
                instrument_id=data['instrument_id'],
                symbol_id=data['symbol_id'],
                from_date=data['from_date'],
                to_date=data['to_date'],
                account_type=data['account_type'],
                fyers_account_id=data.get('fyers_account_id'),
                status='pending'
            )
            
            logger.info(f"Historical data request created: {historical_request.id}")
            
            # TODO: Trigger Celery task
            # from .tasks import fetch_historical_data_task
            # fetch_historical_data_task.delay(historical_request.id)
            
            return Response({
                'status': 'success',
                'message': 'Historical data fetch request submitted successfully',
                'data': {
                    'request_id': historical_request.id,
                    'status': historical_request.status,
                    'estimated_time': '2-5 minutes'
                }
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"Error creating historical data request: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to submit request',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistoricalDataRequestStatusView(APIView):
    """
    Check status of historical data request
    """
    permission_classes = []
    
    def get(self, request, request_id):
        """Get request status"""
        try:
            historical_request = HistoricalDataRequest.objects.using('fyers').get(
                id=request_id
            )
            
            serializer = HistoricalDataRequestSerializer(historical_request)
            
            return Response({
                'status': 'success',
                'message': 'Request status retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except HistoricalDataRequest.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error fetching request status: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch request status',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)