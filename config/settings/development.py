from .base import *  # noqa
from .base import env

DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", default="django-insecure-development-key-!!!"
)
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "localhost",
        "0.0.0.0",  # nosec B104
        "127.0.0.1",
        "192.168.1.90",
        "juniper-fester-married.ngrok-free.dev",
        "156.67.24.4",
    ],
)  # nosec B104
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[
        "https://juniper-fester-married.ngrok-free.dev",
        "http://156.67.24.4:8080",
    ],
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
