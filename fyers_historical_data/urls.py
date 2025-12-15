"""
FYERS Historical Data URLs
"""

from django.urls import path
from .views import (
    ExchangeListView,
    InstrumentListView,
    SymbolListView,
    HistoricalDataRequestView,
    HistoricalDataRequestStatusView,
)

app_name = 'fyers_historical_data'

urlpatterns = [
    # Form options
    path('exchanges/', ExchangeListView.as_view(), name='exchanges'),
    path('instruments/', InstrumentListView.as_view(), name='instruments'),
    path('symbols/', SymbolListView.as_view(), name='symbols'),
    
    # Data fetching
    path('historical/fetch/', HistoricalDataRequestView.as_view(), name='fetch-historical'),
    path('historical/status/<int:request_id>/', HistoricalDataRequestStatusView.as_view(), name='request-status'),
]