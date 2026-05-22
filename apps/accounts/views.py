import uuid

from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import AllowedDomain
from .schemas import (
    company_profile_schema,
    email_verification_schema,
    forgot_password_schema,
    login_schema,
    logout_schema,
    password_reset_schema,
    registration_schema,
)
from .serializers import (
    AllowedDomainSerializer,
    CompanyProfileSerializer,
    EmailVerificationSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
)
from .services import (
    get_or_update_company_profile,
    login_user,
    logout_user,
    register_company_owner,
    request_password_reset,
)
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
        tokens = login_user(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
        )
        if tokens is None:
            return Response({"detail": "Invalid credentials or unverified account."}, status=400)
        return Response(tokens)

    @logout_schema
    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not logout_user(serializer.validated_data["refresh"]):
            return Response({"detail": "Invalid or already blacklisted token."}, status=400)
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

    @action(detail=False, methods=["post"], url_path="embed-token/regenerate", url_name="embed-token-regenerate")
    def regenerate_embed_token(self, request):
        """Issue a fresh embed token, invalidating the previous one."""
        company = get_or_update_company_profile(request.user)
        company.embed_token = uuid.uuid4()
        company.save(update_fields=["embed_token"])
        return Response({"embed_token": str(company.embed_token)})


class AllowedDomainViewSet(ViewSet):
    """CRUD for the list of domains permitted to embed the chat widget."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        company = get_or_update_company_profile(request.user)
        qs = AllowedDomain.objects.filter(company=company)
        return Response(AllowedDomainSerializer(qs, many=True).data)

    def create(self, request):
        company = get_or_update_company_profile(request.user)
        serializer = AllowedDomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.validated_data["domain"].lower().strip()
        obj, created = AllowedDomain.objects.get_or_create(company=company, domain=domain)
        status_code = 201 if created else 200
        return Response(AllowedDomainSerializer(obj).data, status=status_code)

    def destroy(self, request, pk=None):
        company = get_or_update_company_profile(request.user)
        try:
            obj = AllowedDomain.objects.get(pk=pk, company=company)
        except AllowedDomain.DoesNotExist:
            return Response(status=404)
        obj.delete()
        return Response(status=204)
