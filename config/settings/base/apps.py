# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [

    "daphne",  # Must be first — overrides runserver to serve ASGI + WebSockets
    "unfold",  # Must be before django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_extensions",
    "djstripe",
    "channels",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.billing",
    "apps.knowledge",
    "apps.chat",
    "apps.analytics",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
