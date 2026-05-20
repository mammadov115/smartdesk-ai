from drf_spectacular.utils import OpenApiResponse, extend_schema

from .serializers import NotificationPreferenceSerializer

preference_detail_schema = extend_schema(
    summary="Get notification preferences",
    description=(
        "Returns the authenticated user's company notification preferences. "
        "A default preference object is created automatically on first access."
    ),
    responses={200: NotificationPreferenceSerializer},
)

preference_update_schema = extend_schema(
    summary="Update notification preferences",
    description=(
        "Partially update notification preferences for the authenticated user's company. "
        "All fields are optional — only the supplied fields are changed."
    ),
    request=NotificationPreferenceSerializer,
    responses={
        200: NotificationPreferenceSerializer,
        400: OpenApiResponse(description="Validation error."),
    },
)
