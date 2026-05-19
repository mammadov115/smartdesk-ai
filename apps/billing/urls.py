from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("api/billing/checkout/", views.checkout, name="checkout"),
    path("api/billing/portal/", views.portal, name="portal"),
]
