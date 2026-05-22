from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CompanyProfile, User
from .utils import decode_uid, email_verification_token_generator, encode_uid


def _send_mail(subject, message, recipient_email):
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[recipient_email],
    )


def _build_absolute_url(request, path):
    if request is not None:
        return request.build_absolute_uri(path)

    current_site = get_current_site(None)
    return f"https://{current_site.domain}{path}"


@transaction.atomic
def register_company_owner(validated_data, request=None):
    name = validated_data["name"]
    email = validated_data["email"].strip().lower()
    password = validated_data["password"]
    subscription_plan = validated_data.get(
        "subscription_plan",
        CompanyProfile.SubscriptionPlan.FREE,
    )

    validate_password(password)

    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
        is_active=False,
        is_email_verified=False,
    )
    CompanyProfile.objects.create(
        owner=user,
        name=name,
        subscription_plan=subscription_plan,
    )

    verify_path = reverse("accounts:auth-verify-email")
    verify_url = _build_absolute_url(request, verify_path)
    verify_url = f"{verify_url}?uid={encode_uid(user)}&token={email_verification_token_generator.make_token(user)}"
    message = f"Welcome to Smartdesk-ai.\n\nVerify your email by visiting: {verify_url}\n"
    _send_mail("Verify your email", message, user.email)

    return user


@transaction.atomic
def verify_email(uidb64, token):
    try:
        user = User.objects.get(pk=decode_uid(uidb64))
    except ObjectDoesNotExist, ValueError:
        return None

    if not email_verification_token_generator.check_token(user, token):
        return None

    user.is_email_verified = True
    user.is_active = True
    user.save(update_fields=["is_email_verified", "is_active"])
    return user


def login_user(email, password):
    """Authenticate user and return a JWT token pair, or None on failure."""
    user = authenticate(username=email.strip().lower(), password=password)
    if user is None or not user.is_active or not user.is_email_verified:
        return None

    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def logout_user(refresh_token: str) -> bool:
    """Blacklist the provided refresh token. Returns False if token is invalid."""
    try:
        RefreshToken(refresh_token).blacklist()
        return True
    except TokenError:
        return False


@transaction.atomic
def request_password_reset(email, request=None):
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if user is None:
        return None

    reset_path = reverse("accounts:auth-password-reset")
    reset_url = _build_absolute_url(request, reset_path)
    reset_url = f"{reset_url}?uid={encode_uid(user)}&token={default_token_generator.make_token(user)}"
    message = (
        f"We received a password reset request for your account.\n\nReset your password by visiting: {reset_url}\n"
    )
    _send_mail("Reset your password", message, user.email)
    return user


@transaction.atomic
def reset_password(uidb64, token, password):
    try:
        user = User.objects.get(pk=decode_uid(uidb64))
    except ObjectDoesNotExist, ValueError:
        return None

    if not default_token_generator.check_token(user, token):
        return None

    validate_password(password, user=user)
    user.set_password(password)
    user.save(update_fields=["password"])
    return user


@transaction.atomic
def get_or_update_company_profile(user, validated_data=None):
    company_profile, _ = CompanyProfile.objects.get_or_create(
        owner=user,
        defaults={"name": user.name},
    )

    if validated_data:
        for field, value in validated_data.items():
            setattr(company_profile, field, value)
        company_profile.save()

    return company_profile
