import stripe
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .services import (
    create_checkout_session,
    create_portal_session,
    get_current_usage,
    get_invoices,
)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    price_id = request.data.get("price_id")
    if not price_id:
        return Response({"detail": "price_id is required."}, status=400)
    try:
        url = create_checkout_session(request.user, price_id)
    except stripe.StripeError as exc:
        return Response({"detail": str(exc)}, status=400)
    return Response({"checkout_url": url})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def portal(request):
    try:
        url = create_portal_session(request.user)
    except stripe.StripeError as exc:
        return Response({"detail": str(exc)}, status=400)
    return Response({"portal_url": url})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def invoices(request):
    return Response(get_invoices(request.user))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def usage(request):
    return Response(get_current_usage(request.user))
