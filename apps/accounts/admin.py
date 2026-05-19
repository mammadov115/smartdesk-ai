from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter
from unfold.decorators import display

from .models import CompanyProfile
from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        "email",
        "name",
        "display_active",
        "display_email_verified",
        "is_staff",
        "date_joined",
    )
    search_fields = ("email", "name")
    list_filter = (
        ("is_active", ChoicesDropdownFilter),
        ("is_email_verified", ChoicesDropdownFilter),
        ("is_staff", ChoicesDropdownFilter),
    )
    ordering = ("email",)
    readonly_fields = ("date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "name", "password")}),
        (
            "Status",
            {"fields": ("is_active", "is_email_verified", "is_staff", "is_superuser")},
        ),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    @display(boolean=True, description="Active")
    def display_active(self, obj):
        return obj.is_active

    @display(boolean=True, description="Email verified")
    def display_email_verified(self, obj):
        return obj.is_email_verified


@admin.register(CompanyProfile)
class CompanyProfileAdmin(ModelAdmin):
    list_display = ("name", "owner", "display_plan", "updated_at")
    search_fields = ("name", "owner__email", "contact_email")
    list_filter = (("subscription_plan", ChoicesDropdownFilter),)

    @display(description="Plan", label=True)
    def display_plan(self, obj):
        return obj.subscription_plan
