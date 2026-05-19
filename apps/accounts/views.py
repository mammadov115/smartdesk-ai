from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .schemas import company_profile_schema
from .schemas import email_verification_schema
from .schemas import forgot_password_schema
from .schemas import login_schema
from .schemas import logout_schema
from .schemas import password_reset_schema
from .schemas import registration_schema
from .serializers import CompanyProfileSerializer
from .serializers import EmailVerificationSerializer
from .serializers import ForgotPasswordSerializer
from .serializers import LoginSerializer
from .serializers import PasswordResetSerializer
from .serializers import RegistrationSerializer
from .services import get_or_update_company_profile
from .services import login_user
from .services import logout_user
from .services import register_company_owner
from .services import request_password_reset
from .services import reset_password
from .services import verify_email


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @registration_schema
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        register_company_owner(serializer.validated_data, request=request)
        return Response(
            {"detail": "Registration successful. Please verify your email."},
            status=201,
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @email_verification_schema
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = verify_email(
            serializer.validated_data["uid"],
            serializer.validated_data["token"],
        )
        if user is None:
            return Response({"detail": "Invalid or expired verification token."}, status=400)
        return Response({"detail": "Email verified successfully."})


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @login_schema
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = login_user(
            request,
            serializer.validated_data["email"],
            serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": "Invalid credentials or unverified account."}, status=400)
        return Response({"detail": "Logged in successfully."})


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @logout_schema
    def post(self, request):
        logout_user(request)
        return Response({"detail": "Logged out successfully."})


class ForgotPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @forgot_password_schema
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(serializer.validated_data["email"], request=request)
        return Response({"detail": "If the account exists, a reset email has been sent."})


class PasswordResetAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @password_reset_schema
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = reset_password(
            serializer.validated_data["uid"],
            serializer.validated_data["token"],
            serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": "Invalid or expired reset token."}, status=400)
        return Response({"detail": "Password reset successfully."})


class CompanyProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @company_profile_schema
    def get(self, request):
        company_profile = get_or_update_company_profile(request.user)
        serializer = CompanyProfileSerializer(company_profile)
        return Response(serializer.data)

    @company_profile_schema
    def patch(self, request):
        company_profile = get_or_update_company_profile(request.user)
        serializer = CompanyProfileSerializer(
            company_profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        company_profile = get_or_update_company_profile(request.user, serializer.validated_data)
        return Response(CompanyProfileSerializer(company_profile).data)
