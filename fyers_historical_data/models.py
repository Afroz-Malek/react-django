"""
FYERS Historical Data Models
"""

from django.db import models
from django.utils import timezone


class Exchange(models.Model):
    """
    Stock/Commodity Exchanges
    Examples: NSE, BSE, MCX, NCDEX
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fyers_exchanges'
        ordering = ['display_order', 'name']
        verbose_name = 'Exchange'
        verbose_name_plural = 'Exchanges'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Instrument(models.Model):
    """
    Trading Instruments
    Examples: Stocks, Stock Options, Index, etc.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fyers_instruments'
        ordering = ['display_order', 'name']
        verbose_name = 'Instrument'
        verbose_name_plural = 'Instruments'
    
    def __str__(self):
        return self.name


class Symbol(models.Model):
    """
    Trading Symbols for each Exchange and Instrument combination
    Examples: NSE:RELIANCE-EQ, BSE:500325, etc.
    """
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='symbols')
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name='symbols')
    
    # Symbol details
    symbol_code = models.CharField(max_length=50)
    symbol_name = models.CharField(max_length=255)
    fyers_symbol = models.CharField(max_length=100, unique=True)
    
    # Additional details
    isin = models.CharField(max_length=50, blank=True, null=True)
    lot_size = models.IntegerField(default=1)
    tick_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.05)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fyers_symbols'
        ordering = ['symbol_name']
        unique_together = ['exchange', 'instrument', 'symbol_code']
        indexes = [
            models.Index(fields=['exchange', 'instrument', 'is_active']),
            models.Index(fields=['symbol_code']),
            models.Index(fields=['fyers_symbol']),
        ]
        verbose_name = 'Symbol'
        verbose_name_plural = 'Symbols'
    
    def __str__(self):
        return f"{self.symbol_code} - {self.symbol_name}"


class HistoricalDataRequest(models.Model):
    """
    User requests for historical data fetching
    """
    # User info (email from stockstarauthversionone)
    user_email = models.EmailField()
    
    # Form selections
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    
    # Date range
    from_date = models.DateField()
    to_date = models.DateField()
    
    # Account selection
    ACCOUNT_TYPE_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('specific', 'Specific Account'),
    ]
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    fyers_account_id = models.IntegerField(blank=True, null=True)
    
    # Request status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    
    # Result details
    result_file_path = models.CharField(max_length=500, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    file_size_kb = models.IntegerField(default=0)
    processing_time_seconds = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'fyers_historical_data_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_email', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'Historical Data Request'
        verbose_name_plural = 'Historical Data Requests'
    
    def __str__(self):
        return f"{self.user_email} - {self.symbol.symbol_code} ({self.status})"


class HistoricalDataCache(models.Model):
    """
    Cache for historical data to avoid repeated API calls
    """
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Cached data (JSON format)
    data = models.JSONField()
    
    # Cache metadata
    cached_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    hit_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'fyers_historical_data_cache'
        unique_together = ['exchange', 'symbol', 'date']
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['symbol', 'date']),
        ]
        verbose_name = 'Data Cache'
        verbose_name_plural = 'Data Cache'
    
    def __str__(self):
        return f"{self.symbol.symbol_code} - {self.date}"