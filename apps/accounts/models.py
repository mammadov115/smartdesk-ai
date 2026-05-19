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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
