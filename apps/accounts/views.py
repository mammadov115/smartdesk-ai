from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

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
from .services import reset_password as reset_password_service
from .services import verify_email as verify_email_service


class AuthViewSet(ViewSet):
    permission_classes = [permissions.AllowAny]

    @registration_schema
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        register_company_owner(serializer.validated_data, request=request)
        return Response(
            {"detail": "Registration successful. Please verify your email."},
            status=201,
        )

    @email_verification_schema
    @action(detail=False, methods=["post"], url_path="verify-email", url_name="verify-email")
    def verify_email(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = verify_email_service(
            serializer.validated_data["uid"],
            serializer.validated_data["token"],
        )
        if user is None:
            return Response({"detail": "Invalid or expired verification token."}, status=400)
        return Response({"detail": "Email verified successfully."})

    @login_schema
    @action(detail=False, methods=["post"])
    def login(self, request):
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

    @logout_schema
    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        logout_user(request)
        return Response({"detail": "Logged out successfully."})

    @forgot_password_schema
    @action(detail=False, methods=["post"], url_path="password/forgot", url_name="password-forgot")
    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(serializer.validated_data["email"], request=request)
        return Response({"detail": "If the account exists, a reset email has been sent."})

    @password_reset_schema
    @action(detail=False, methods=["post"], url_path="password/reset", url_name="password-reset")
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = reset_password_service(
            serializer.validated_data["uid"],
            serializer.validated_data["token"],
            serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": "Invalid or expired reset token."}, status=400)
        return Response({"detail": "Password reset successfully."})


class CompanyProfileViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @company_profile_schema
    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        if request.method == "GET":
            company_profile = get_or_update_company_profile(request.user)
            serializer = CompanyProfileSerializer(company_profile)
            return Response(serializer.data)

        company_profile = get_or_update_company_profile(request.user)
        serializer = CompanyProfileSerializer(
            company_profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        company_profile = get_or_update_company_profile(request.user, serializer.validated_data)
        return Response(CompanyProfileSerializer(company_profile).data)
