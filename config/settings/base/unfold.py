
# UNFOLD ADMIN
# ------------------------------------------------------------------------------
# https://unfoldadmin.com/docs/configuration/
from django.urls import reverse_lazy  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

UNFOLD = {
    "DASHBOARD_CALLBACK": "apps.accounts.dashboard.dashboard_callback",
    "SITE_TITLE": "Smartdesk-ai",
    "SITE_HEADER": "Smartdesk-ai",
    "SITE_SUBHEADER": _("Administration"),
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "BORDER_RADIUS": "8px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(96.7% .003 264.542)",
            "200": "oklch(92.8% .006 264.531)",
            "300": "oklch(87.2% .01 258.338)",
            "400": "oklch(70.7% .022 261.325)",
            "500": "oklch(55.1% .027 264.364)",
            "600": "oklch(44.6% .03 256.802)",
            "700": "oklch(37.3% .034 259.733)",
            "800": "oklch(27.8% .033 256.848)",
            "900": "oklch(21% .034 264.665)",
            "950": "oklch(13% .028 261.692)",
        },
        "primary": {
            "50": "oklch(97.8% .015 250)",
            "100": "oklch(94.5% .038 252)",
            "200": "oklch(88.9% .075 254)",
            "300": "oklch(80.9% .127 256)",
            "400": "oklch(69.8% .185 258)",
            "500": "oklch(58.5% .22 261)",
            "600": "oklch(50.6% .214 263)",
            "700": "oklch(43.9% .188 265)",
            "800": "oklch(38.2% .151 267)",
            "900": "oklch(32.8% .115 268)",
            "950": "oklch(24.5% .085 269)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Dashboard"),
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Users & Auth"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Billing"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Customers"),
                        "icon": "credit_card",
                        "link": reverse_lazy("admin:djstripe_customer_changelist"),
                    },
                    {
                        "title": _("Subscriptions"),
                        "icon": "autorenew",
                        "link": reverse_lazy("admin:djstripe_subscription_changelist"),
                    },
                    {
                        "title": _("Invoices"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:djstripe_invoice_changelist"),
                    },
                ],
            },
            {
                "title": _("Knowledge Base"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Documents"),
                        "icon": "description",
                        "link": reverse_lazy("admin:knowledge_knowledgedocument_changelist"),
                    },
                ],
            },
        ],
    },
}
