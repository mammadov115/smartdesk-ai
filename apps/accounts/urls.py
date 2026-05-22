from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AllowedDomainViewSet, AuthViewSet, CompanyProfileViewSet

app_name = "accounts"

router = SimpleRouter()
router.register("api/auth", AuthViewSet, basename="auth")
router.register("api/company", CompanyProfileViewSet, basename="company")
router.register(
    "api/company/domains", AllowedDomainViewSet, basename="allowed-domain"
)

urlpatterns = [
    path("", include(router.urls)),
]
