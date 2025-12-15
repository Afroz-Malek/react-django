"""
URL configuration for stockstar_backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from stockstarauthversionone.fyers_views import fyers_callback


def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'StockstarCapital Backend API',
        'version': '1.0.0'
    })


urlpatterns = [
    # Fyers callback
    path("fyers-callback/", fyers_callback, name="fyers_callback"),

    # Admin interface
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check, name='health_check'),

    # Authentication API endpoints
    path('api/authentication/', include('stockstarauthversionone.urls')),
    path('api/fyers/', include('fyers_auth.urls')),  # App 2 - Add this here
    path('api/fyers-data/', include('fyers_historical_data.urls')),

]

# Customize admin site
admin.site.site_header = 'StockstarCapital Administration'
admin.site.site_title = 'StockstarCapital Admin'
admin.site.index_title = 'Welcome to StockstarCapital Backend'
