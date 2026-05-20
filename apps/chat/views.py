import logging

from rest_framework import mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import ChatMessage, ChatSession
from .serializers import AskSerializer, ChatMessageSerializer, ChatSessionSerializer
from .services import FALLBACK_ANSWER, answer_question, escalate_to_operator

logger = logging.getLogger(__name__)


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
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def ask(self, request, pk=None):
        session = self.get_object()

        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        # Persist the user turn
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=question,
        )

        # Resolve company profile (gracefully handles missing profiles)
        company_profile = getattr(request.user, "company_profile", None)

        # Run the RAG pipeline; fall back gracefully on unexpected errors
        try:
            result = answer_question(question, request.user, company_profile)
        except Exception:
            logger.exception("RAG pipeline error for session %s", session.pk)
            result = {"answer": FALLBACK_ANSWER, "sources": []}

        # Persist the assistant turn
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=result["answer"],
            sources=result["sources"],
        )

        # Escalate to operator on the first fallback in this session
        if result.get("is_fallback") and session.status == ChatSession.Status.AI:
            try:
                escalate_to_operator(session)
            except Exception:
                logger.exception("Failed to escalate session %s to operator", session.pk)

        return Response(
            ChatMessageSerializer(assistant_msg).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        session = self.get_object()
        msgs = session.messages.order_by("created_at")
        return Response(ChatMessageSerializer(msgs, many=True).data)
