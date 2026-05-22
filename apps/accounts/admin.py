from django.contrib import admin
from django.contrib import messages
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter
from unfold.decorators import action as unfold_action
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
    list_display = ("name", "owner", "display_plan", "display_owner_active", "updated_at")
    search_fields = ("name", "owner__email", "contact_email")
    list_filter = (("subscription_plan", ChoicesDropdownFilter),)
    actions = ["block_companies", "activate_companies", "set_plan_paid", "set_plan_free"]

    @display(description="Plan", label=True)
    def display_plan(self, obj):
        return obj.subscription_plan

    @display(boolean=True, description="Active")
    def display_owner_active(self, obj):
        return obj.owner.is_active

    @unfold_action(description="Block selected companies (deactivate owner accounts)")
    def block_companies(self, request, queryset):
        updated = User.objects.filter(
            pk__in=queryset.values("owner_id"), is_active=True
        ).update(is_active=False)
        self.message_user(request, f"{updated} company owner(s) blocked.", messages.WARNING)

    @unfold_action(description="Activate selected companies (re-enable owner accounts)")
    def activate_companies(self, request, queryset):
        updated = User.objects.filter(
            pk__in=queryset.values("owner_id"), is_active=False
        ).update(is_active=True)
        self.message_user(request, f"{updated} company owner(s) activated.", messages.SUCCESS)

    @unfold_action(description="Change plan → Paid")
    def set_plan_paid(self, request, queryset):
        updated = queryset.filter(
            subscription_plan=CompanyProfile.SubscriptionPlan.FREE
        ).update(subscription_plan=CompanyProfile.SubscriptionPlan.PAID)
        self.message_user(request, f"{updated} company plan(s) upgraded to Paid.", messages.SUCCESS)

    @unfold_action(description="Change plan → Free")
    def set_plan_free(self, request, queryset):
        updated = queryset.filter(
            subscription_plan=CompanyProfile.SubscriptionPlan.PAID
        ).update(subscription_plan=CompanyProfile.SubscriptionPlan.FREE)
        self.message_user(request, f"{updated} company plan(s) downgraded to Free.", messages.WARNING)
