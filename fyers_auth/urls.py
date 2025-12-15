from django.urls import path
from .views import GenerateAccessTokenView, VerifyTokenView, UserTokensView, GetProfileView

urlpatterns = [
    path('generate-token/', GenerateAccessTokenView.as_view(), name='generate-token'),
    path('get-profile/', GetProfileView.as_view(), name='get-profile'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('user-tokens/', UserTokensView.as_view(), name='user-tokens'),
]