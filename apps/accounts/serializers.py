from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CompanyProfile
from .models import User


class RegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    subscription_plan = serializers.ChoiceField(
        choices=CompanyProfile.SubscriptionPlan.choices,
        required=False,
        default=CompanyProfile.SubscriptionPlan.FREE,
    )

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        validate_password(value)
        return value


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = (
            "name",
            "logo",
            "contact_email",
            "phone_number",
            "website",
            "address",
            "subscription_plan",
            "chat_name",
            "greeting_message",
            "chat_language",
        )
        extra_kwargs = {
            "name": {"required": False},
            "contact_email": {"required": False, "allow_blank": True},
            "phone_number": {"required": False, "allow_blank": True},
            "website": {"required": False, "allow_blank": True},
            "address": {"required": False, "allow_blank": True},
            "logo": {"required": False, "allow_null": True},
            "subscription_plan": {"required": False},
            "chat_name": {"required": False},
            "greeting_message": {"required": False},
            "chat_language": {"required": False, "allow_blank": True},
        }
