from rest_framework import mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.accounts.models import CompanyProfile
from apps.accounts.serializers import WidgetConfigSerializer

from .models import ChatSession
from .serializers import (
    AskSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
)
from .services import (
    check_session_creation_allowed,
    handle_ask,
    record_session_created,
)


class WidgetConfigView(APIView):
    """
    Public endpoint — no authentication required.
    Returns the chat widget appearance settings for the given embed token.
    Used by the frontend script tag to style the widget before load.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, embed_token):
        try:
            company = CompanyProfile.objects.get(embed_token=embed_token)
        except CompanyProfile.DoesNotExist:
            return Response(status=404)
        return Response(WidgetConfigSerializer(company).data)


class ChatSessionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """
    list:    List all chat sessions for the authenticated user.
    create:  Start a new chat session. Returns chat_name + greeting_message
             pulled from the user's CompanyProfile.
    retrieve: Get a single session.
    ask:     POST /api/chat/sessions/{id}/ask/ — send a question, run the
             RAG pipeline, and return the assistant's reply with sources.
    messages: GET /api/chat/sessions/{id}/messages/ — full message history.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "ask":
            return AskSerializer
        return ChatSessionSerializer

    def perform_create(self, serializer):
        check_session_creation_allowed(self.request.user)
        serializer.save(owner=self.request.user)
        record_session_created(self.request.user)

    @action(detail=True, methods=["post"])
    def ask(self, request, pk=None):
        session = self.get_object()

        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        assistant_msg = handle_ask(session, question, request.user)

        return Response(
            ChatMessageSerializer(assistant_msg).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        session = self.get_object()
        msgs = session.messages.order_by("created_at")
        return Response(ChatMessageSerializer(msgs, many=True).data)
