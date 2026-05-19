from django.urls import include
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AuthViewSet
from .views import CompanyProfileViewSet

app_name = "accounts"

router = SimpleRouter()
router.register("api/auth", AuthViewSet, basename="auth")
router.register("api/company", CompanyProfileViewSet, basename="company")

urlpatterns = [
    path("", include(router.urls)),
]
