import djstripe.models
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter
from unfold.decorators import display

# dj-stripe registers its own admin for every model. Unregister the ones we
# want to own so we can apply Unfold styling without conflicts.
for _model in (
    djstripe.models.Customer,
    djstripe.models.Subscription,
    djstripe.models.Invoice,
):
    try:
        admin.site.unregister(_model)
    except admin.sites.NotRegistered:
        pass


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


@admin.register(djstripe.models.Customer)
class CustomerAdmin(ModelAdmin):
    list_display = (
        "id",
        "display_subscriber",
        "email",
        "livemode",
        "created",
    )
    search_fields = ("id", "email", "subscriber__email")
    list_filter = (("livemode", ChoicesDropdownFilter),)
    ordering = ("-created",)
    readonly_fields = (
        "id",
        "djstripe_id",
        "djstripe_owner_account",
        "livemode",
        "created",
        "djstripe_created",
        "djstripe_updated",
        "email",
        "default_payment_method",
        "subscriber",
        "date_purged",
        "metadata",
        "stripe_data",
    )

    fieldsets = (
        (
            "Stripe",
            {"fields": ("id", "livemode", "created", "djstripe_owner_account")},
        ),
        (
            "Subscriber",
            {"fields": ("subscriber", "email", "default_payment_method", "date_purged")},
        ),
        (
            "Metadata",
            {"fields": ("metadata",), "classes": ("collapse",)},
        ),
        (
            "Raw Stripe data",
            {"fields": ("stripe_data",), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description="Subscriber")
    def display_subscriber(self, obj):
        return obj.subscriber or "—"


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

_SUB_STATUS_LABELS = {
    "active": "success",
    "trialing": "info",
    "past_due": "warning",
    "incomplete": "warning",
    "incomplete_expired": "danger",
    "unpaid": "danger",
    "canceled": "danger",
    "paused": "warning",
}


@admin.register(djstripe.models.Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = (
        "id",
        "display_customer_email",
        "display_status",
        "display_period_end",
        "created",
    )
    search_fields = ("id", "customer__email", "customer__subscriber__email")
    list_filter = (("livemode", ChoicesDropdownFilter),)
    date_hierarchy = "created"
    ordering = ("-created",)
    readonly_fields = (
        "id",
        "djstripe_id",
        "djstripe_owner_account",
        "livemode",
        "created",
        "djstripe_created",
        "djstripe_updated",
        "customer",
        "metadata",
        "stripe_data",
        # stripe_data-sourced display helpers shown in the change view
        "display_status",
        "display_period_start",
        "display_period_end",
        "display_cancel_at_period_end",
        "display_canceled_at",
        "display_trial_start",
        "display_trial_end",
    )

    fieldsets = (
        (
            "Stripe",
            {"fields": ("id", "livemode", "created", "display_status")},
        ),
        (
            "Customer",
            {"fields": ("customer",)},
        ),
        (
            "Billing cycle",
            {
                "fields": (
                    "display_period_start",
                    "display_period_end",
                    "display_cancel_at_period_end",
                    "display_canceled_at",
                )
            },
        ),
        (
            "Trial",
            {
                "fields": ("display_trial_start", "display_trial_end"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("metadata",), "classes": ("collapse",)},
        ),
        (
            "Raw Stripe data",
            {"fields": ("stripe_data",), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _sd(self, obj):
        return obj.stripe_data or {}

    @display(description="Customer")
    def display_customer_email(self, obj):
        return obj.customer.email or obj.customer_id

    @display(description="Status", label=_SUB_STATUS_LABELS)
    def display_status(self, obj):
        return self._sd(obj).get("status", "—")

    @display(description="Period start")
    def display_period_start(self, obj):
        return self._sd(obj).get("current_period_start", "—")

    @display(description="Period end")
    def display_period_end(self, obj):
        return self._sd(obj).get("current_period_end", "—")

    @display(description="Cancel at period end")
    def display_cancel_at_period_end(self, obj):
        return self._sd(obj).get("cancel_at_period_end", "—")

    @display(description="Canceled at")
    def display_canceled_at(self, obj):
        return self._sd(obj).get("canceled_at") or "—"

    @display(description="Trial start")
    def display_trial_start(self, obj):
        return self._sd(obj).get("trial_start") or "—"

    @display(description="Trial end")
    def display_trial_end(self, obj):
        return self._sd(obj).get("trial_end") or "—"


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

_INV_STATUS_LABELS = {
    "draft": "info",
    "open": "warning",
    "paid": "success",
    "uncollectible": "danger",
    "void": "danger",
}


@admin.register(djstripe.models.Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = (
        "id",
        "display_customer_email",
        "display_status",
        "display_total",
        "display_paid",
        "created",
    )
    search_fields = ("id", "customer__email", "customer__subscriber__email")
    list_filter = (("livemode", ChoicesDropdownFilter),)
    date_hierarchy = "created"
    ordering = ("-created",)
    readonly_fields = (
        "id",
        "djstripe_id",
        "djstripe_owner_account",
        "livemode",
        "created",
        "djstripe_created",
        "djstripe_updated",
        "charge",
        "customer",
        "default_payment_method",
        "payment_intent",
        "subscription",
        "metadata",
        "stripe_data",
        # stripe_data-sourced display helpers shown in the change view
        "display_status",
        "display_currency",
        "display_subtotal",
        "display_tax",
        "display_total",
        "display_amount_due",
        "display_amount_paid",
        "display_amount_remaining",
        "display_due_date",
        "display_period_start",
        "display_period_end",
        "display_hosted_url",
        "display_invoice_pdf",
    )

    fieldsets = (
        (
            "Stripe",
            {"fields": ("id", "livemode", "created", "display_status")},
        ),
        (
            "Customer & subscription",
            {"fields": ("customer", "subscription", "charge", "payment_intent")},
        ),
        (
            "Amounts",
            {
                "fields": (
                    "display_currency",
                    "display_subtotal",
                    "display_tax",
                    "display_total",
                    "display_amount_due",
                    "display_amount_paid",
                    "display_amount_remaining",
                )
            },
        ),
        (
            "Dates",
            {"fields": ("display_due_date", "display_period_start", "display_period_end")},
        ),
        (
            "Links",
            {
                "fields": ("display_hosted_url", "display_invoice_pdf"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("metadata",), "classes": ("collapse",)},
        ),
        (
            "Raw Stripe data",
            {"fields": ("stripe_data",), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _sd(self, obj):
        return obj.stripe_data or {}

    def _money(self, obj, key):
        val = self._sd(obj).get(key)
        if val is None:
            return "—"
        currency = self._sd(obj).get("currency", "usd").upper()
        return f"{val / 100:.2f} {currency}"

    @display(description="Customer")
    def display_customer_email(self, obj):
        return obj.customer.email or obj.customer_id

    @display(description="Status", label=_INV_STATUS_LABELS)
    def display_status(self, obj):
        return self._sd(obj).get("status", "—")

    @display(description="Paid", boolean=True)
    def display_paid(self, obj):
        return bool(self._sd(obj).get("paid", False))

    @display(description="Total")
    def display_total(self, obj):
        return self._money(obj, "total")

    @display(description="Currency")
    def display_currency(self, obj):
        return self._sd(obj).get("currency", "—").upper()

    @display(description="Subtotal")
    def display_subtotal(self, obj):
        return self._money(obj, "subtotal")

    @display(description="Tax")
    def display_tax(self, obj):
        return self._money(obj, "tax")

    @display(description="Amount due")
    def display_amount_due(self, obj):
        return self._money(obj, "amount_due")

    @display(description="Amount paid")
    def display_amount_paid(self, obj):
        return self._money(obj, "amount_paid")

    @display(description="Amount remaining")
    def display_amount_remaining(self, obj):
        return self._money(obj, "amount_remaining")

    @display(description="Due date")
    def display_due_date(self, obj):
        return self._sd(obj).get("due_date") or "—"

    @display(description="Period start")
    def display_period_start(self, obj):
        return self._sd(obj).get("period_start") or "—"

    @display(description="Period end")
    def display_period_end(self, obj):
        return self._sd(obj).get("period_end") or "—"

    @display(description="Invoice URL")
    def display_hosted_url(self, obj):
        return self._sd(obj).get("hosted_invoice_url") or "—"

    @display(description="Invoice PDF")
    def display_invoice_pdf(self, obj):
        return self._sd(obj).get("invoice_pdf") or "—"
