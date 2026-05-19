from drf_spectacular.utils import OpenApiResponse
from drf_spectacular.utils import extend_schema

from .serializers import CompanyProfileSerializer
from .serializers import EmailVerificationSerializer
from .serializers import ForgotPasswordSerializer
from .serializers import LoginSerializer
from .serializers import PasswordResetSerializer
from .serializers import RegistrationSerializer


registration_schema = extend_schema(
    summary="Register a company owner",
    request=RegistrationSerializer,
    responses={201: OpenApiResponse(description="Verification email sent.")},
)

email_verification_schema = extend_schema(
    summary="Verify email address",
    request=EmailVerificationSerializer,
    responses={200: OpenApiResponse(description="Email verified.")},
)

login_schema = extend_schema(
    summary="Log in",
    request=LoginSerializer,
    responses={200: OpenApiResponse(description="Logged in successfully.")},
)

logout_schema = extend_schema(
    summary="Log out",
    responses={200: OpenApiResponse(description="Logged out successfully.")},
)

forgot_password_schema = extend_schema(
    summary="Request password reset",
    request=ForgotPasswordSerializer,
    responses={200: OpenApiResponse(description="Reset email sent if the account exists.")},
)

password_reset_schema = extend_schema(
    summary="Reset password",
    request=PasswordResetSerializer,
    responses={200: OpenApiResponse(description="Password reset successfully.")},
)

company_profile_schema = extend_schema(
    summary="View or update company profile",
    request=CompanyProfileSerializer,
    responses={200: CompanyProfileSerializer},
)
