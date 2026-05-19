from django.urls import path

from .views import CompanyProfileAPIView
from .views import ForgotPasswordAPIView
from .views import LoginAPIView
from .views import LogoutAPIView
from .views import PasswordResetAPIView
from .views import RegisterAPIView
from .views import VerifyEmailAPIView

app_name = "accounts"

urlpatterns = [
    path("api/auth/register/", RegisterAPIView.as_view(), name="register"),
    path("api/auth/verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("api/auth/login/", LoginAPIView.as_view(), name="login"),
    path("api/auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path("api/auth/password/forgot/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("api/auth/password/reset/", PasswordResetAPIView.as_view(), name="reset-password"),
    path("api/company/me/", CompanyProfileAPIView.as_view(), name="company-me"),
]
