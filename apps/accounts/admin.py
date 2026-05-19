from django.contrib import admin

from .models import CompanyProfile
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "name",
        "is_active",
        "is_email_verified",
        "is_staff",
        "date_joined",
    )
    search_fields = ("email", "name")
    list_filter = ("is_active", "is_email_verified", "is_staff")
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


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "subscription_plan", "updated_at")
    search_fields = ("name", "owner__email", "contact_email")
    list_filter = ("subscription_plan",)
