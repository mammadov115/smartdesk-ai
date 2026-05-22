from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.chat.models import ChatSession

from .schemas import (
    conversation_detail_schema,
    conversation_list_schema,
    most_asked_schema,
    stats_schema,
    unanswered_schema,
)
from .serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    MostAskedQuestionSerializer,
    StatsSerializer,
    UnansweredQuestionSerializer,
)
from .services import (
    get_conversation_detail,
    get_conversations,
    get_most_asked_questions,
    get_stats,
    get_unanswered_questions,
)


class ConversationViewSet(ViewSet):
    """
    list:     GET /api/analytics/conversations/
    retrieve: GET /api/analytics/conversations/{pk}/
    """

    permission_classes = [permissions.IsAuthenticated]

    @conversation_list_schema
    def list(self, request):
        data = get_conversations(request.user)
        serializer = ConversationSerializer(data, many=True)
        return Response(serializer.data)

    @conversation_detail_schema
    def retrieve(self, request, pk=None):
        try:
            data = get_conversation_detail(request.user, int(pk))
        except ChatSession.DoesNotExist:
            return Response(status=404)
        serializer = ConversationDetailSerializer(data)
        return Response(serializer.data)


class QuestionViewSet(ViewSet):
    """
    most_asked: GET /api/analytics/questions/most-asked/
    unanswered: GET /api/analytics/questions/unanswered/
    """

    permission_classes = [permissions.IsAuthenticated]

    @most_asked_schema
    @action(
        detail=False,
        methods=["get"],
        url_path="most-asked",
        url_name="most-asked",
    )
    def most_asked(self, request):
        data = get_most_asked_questions(request.user)
        serializer = MostAskedQuestionSerializer(data, many=True)
        return Response(serializer.data)

    @unanswered_schema
    @action(
        detail=False,
        methods=["get"],
        url_path="unanswered",
        url_name="unanswered",
    )
    def unanswered(self, request):
        data = get_unanswered_questions(request.user)
        serializer = UnansweredQuestionSerializer(data, many=True)
        return Response(serializer.data)


class StatsViewSet(ViewSet):
    """
    list: GET /api/analytics/stats/?period=daily|weekly|monthly
    """

    permission_classes = [permissions.IsAuthenticated]

    @stats_schema
    def list(self, request):
        period = request.query_params.get("period", "daily")
        data = get_stats(request.user, period)
        serializer = StatsSerializer(data, many=True)
        return Response(serializer.data)
