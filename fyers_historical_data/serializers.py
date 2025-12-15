"""
FYERS Historical Data Serializers
"""

from rest_framework import serializers
from .models import Exchange, Instrument, Symbol, HistoricalDataRequest


class ExchangeSerializer(serializers.ModelSerializer):
    """Serializer for Exchange model"""
    
    class Meta:
        model = Exchange
        fields = ['id', 'code', 'name', 'is_active', 'display_order']


class InstrumentSerializer(serializers.ModelSerializer):
    """Serializer for Instrument model"""
    
    class Meta:
        model = Instrument
        fields = ['id', 'code', 'name', 'is_active', 'display_order']


class SymbolSerializer(serializers.ModelSerializer):
    """Serializer for Symbol model"""
    
    exchange_code = serializers.CharField(source='exchange.code', read_only=True)
    instrument_code = serializers.CharField(source='instrument.code', read_only=True)
    display_text = serializers.SerializerMethodField()
    
    class Meta:
        model = Symbol
        fields = [
            'id',
            'symbol_code',
            'symbol_name',
            'fyers_symbol',
            'exchange_code',
            'instrument_code',
            'display_text',
            'lot_size',
            'tick_size',
        ]
    
    def get_display_text(self, obj):
        """Return formatted display text for dropdown"""
        return f"{obj.symbol_code} - {obj.symbol_name}"


class HistoricalDataRequestSerializer(serializers.ModelSerializer):
    """Serializer for Historical Data Request"""
    
    # Read-only fields for response
    exchange_name = serializers.CharField(source='exchange.name', read_only=True)
    instrument_name = serializers.CharField(source='instrument.name', read_only=True)
    symbol_name = serializers.CharField(source='symbol.symbol_name', read_only=True)
    
    class Meta:
        model = HistoricalDataRequest
        fields = [
            'id',
            'user_email',
            'exchange',
            'exchange_name',
            'instrument',
            'instrument_name',
            'symbol',
            'symbol_name',
            'from_date',
            'to_date',
            'account_type',
            'fyers_account_id',
            'status',
            'total_records',
            'file_size_kb',
            'processing_time_seconds',
            'created_at',
            'processed_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'total_records',
            'file_size_kb',
            'processing_time_seconds',
            'created_at',
            'processed_at',
        ]
    
    def validate(self, data):
        """Validate the request data"""
        # Validate date range
        if data['to_date'] < data['from_date']:
            raise serializers.ValidationError({
                'to_date': 'To date must be greater than or equal to from date'
            })
        
        # Validate specific account is provided when account_type is 'specific'
        if data['account_type'] == 'specific' and not data.get('fyers_account_id'):
            raise serializers.ValidationError({
                'fyers_account_id': 'Please select a specific account'
            })
        
        # Validate symbol belongs to selected exchange and instrument
        if data['symbol'].exchange != data['exchange']:
            raise serializers.ValidationError({
                'symbol': 'Selected symbol does not belong to selected exchange'
            })
        
        if data['symbol'].instrument != data['instrument']:
            raise serializers.ValidationError({
                'symbol': 'Selected symbol does not belong to selected instrument'
            })
        
        return data


class HistoricalDataRequestCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating requests"""
    
    exchange_id = serializers.IntegerField(required=True)
    instrument_id = serializers.IntegerField(required=True)
    symbol_id = serializers.IntegerField(required=True)
    from_date = serializers.DateField(required=True)
    to_date = serializers.DateField(required=True)
    account_type = serializers.ChoiceField(
        choices=['round_robin', 'specific'],
        required=True
    )
    fyers_account_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate(self, data):
        """Validate the request data"""
        # Validate date range
        if data['to_date'] < data['from_date']:
            raise serializers.ValidationError({
                'to_date': 'To date must be greater than or equal to from date'
            })
        
        # Validate specific account
        if data['account_type'] == 'specific' and not data.get('fyers_account_id'):
            raise serializers.ValidationError({
                'fyers_account_id': 'Please select a specific account when using specific account type'
            })
        
        # Validate IDs exist
        try:
            exchange = Exchange.objects.get(id=data['exchange_id'])
        except Exchange.DoesNotExist:
            raise serializers.ValidationError({'exchange_id': 'Invalid exchange selected'})
        
        try:
            instrument = Instrument.objects.get(id=data['instrument_id'])
        except Instrument.DoesNotExist:
            raise serializers.ValidationError({'instrument_id': 'Invalid instrument selected'})
        
        try:
            symbol = Symbol.objects.get(id=data['symbol_id'])
        except Symbol.DoesNotExist:
            raise serializers.ValidationError({'symbol_id': 'Invalid symbol selected'})
        
        # Validate symbol belongs to exchange and instrument
        if symbol.exchange != exchange:
            raise serializers.ValidationError({
                'symbol_id': 'Selected symbol does not belong to selected exchange'
            })
        
        if symbol.instrument != instrument:
            raise serializers.ValidationError({
                'symbol_id': 'Selected symbol does not belong to selected instrument'
            })
        
        return data