from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import NotificationPreference
from .schemas import preference_detail_schema, preference_update_schema
from .serializers import NotificationPreferenceSerializer


class NotificationPreferenceViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_prefs(self, user) -> NotificationPreference:
        company = user.company_profile
        prefs, _ = NotificationPreference.objects.get_or_create(company=company)
        return prefs

    @preference_detail_schema
    @preference_update_schema
    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        prefs = self._get_prefs(request.user)

        if request.method == "GET":
            return Response(NotificationPreferenceSerializer(prefs).data)

        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
