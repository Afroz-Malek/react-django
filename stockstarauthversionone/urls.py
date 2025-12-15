"""
URL Configuration for StockstarAuthVersionOne App
"""

from django.urls import path, include  # Add 'include' here
from .views import (
    StockstarCapitalUserCreationVersionOne,
    StockstarCapitalUserDetailVersionOne
)

app_name = 'stockstarauthversionone'

urlpatterns = [
    # Main authentication endpoints
    path(
        'stockstarcapital-usercreation-versionone/<str:action>/',
        StockstarCapitalUserCreationVersionOne.as_view(),
        name='auth-actions'
    ),
    
    # User detail endpoints (with cache prevention)
    path(
        'stockstarcapital-usercreation-versionone/user/',
        StockstarCapitalUserDetailVersionOne.as_view(),
        name='current-user-detail'
    ),
    path(
        'stockstarcapital-usercreation-versionone/user/<int:user_id>/',
        StockstarCapitalUserDetailVersionOne.as_view(),
        name='user-detail'
    ),
]