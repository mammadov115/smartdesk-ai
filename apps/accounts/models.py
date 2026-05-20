import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email


class CompanyProfile(models.Model):
    class SubscriptionPlan(models.TextChoices):
        FREE = "free", "Free"
        PAID = "paid", "Paid"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_profile",
    )
    name = models.CharField(max_length=255)
    logo = models.FileField(upload_to="company-logos/", blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    subscription_plan = models.CharField(
        max_length=10,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.FREE,
    )
    # AI chat widget settings
    chat_name = models.CharField(max_length=255, default="AI Assistant")
    greeting_message = models.TextField(default="Hello! How can I help you today?")
    chat_language = models.CharField(
        max_length=100,
        blank=True,
        help_text="Language the AI should respond in (e.g. 'Azerbaijani'). Leave blank for default.",
    )
    # Widget embed settings
    embed_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    chat_color = models.CharField(max_length=7, default="#0070f3", help_text="Hex colour for the chat widget.")
    chat_icon = models.ImageField(upload_to="chat-icons/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AllowedDomain(models.Model):
    """
    Domains that are permitted to embed this company's chat widget.
    The WebSocket middleware validates the Origin header against this list.
    """

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="allowed_domains",
    )
    domain = models.CharField(
        max_length=253,
        help_text="Hostname only, no scheme (e.g. acme.com).",
    )

    class Meta:
        unique_together = ("company", "domain")

    def __str__(self):
        return self.domain
