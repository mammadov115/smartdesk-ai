from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from .serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    MostAskedQuestionSerializer,
    StatsSerializer,
    UnansweredQuestionSerializer,
)

conversation_list_schema = extend_schema(
    summary="List conversations",
    description="All chat sessions for the authenticated user with aggregate metadata.",
    responses={200: ConversationSerializer(many=True)},
)

conversation_detail_schema = extend_schema(
    summary="Retrieve a conversation",
    description="Session metadata plus the full message history in chronological order.",
    responses={
        200: ConversationDetailSerializer,
        404: OpenApiResponse(description="Session not found."),
    },
)

most_asked_schema = extend_schema(
    summary="Most asked questions",
    description=(
        "Groups semantically similar user questions by cosine similarity on stored "
        "embeddings (text-embedding-3-small, 1536 dims). Returns up to 10 clusters "
        "sorted by frequency. Questions without a stored embedding are excluded."
    ),
    responses={200: MostAskedQuestionSerializer(many=True)},
)

unanswered_schema = extend_schema(
    summary="Unanswered questions",
    description=(
        "Returns the last user message from each session that was escalated to an "
        "operator (status WAITING or LIVE) — i.e. questions the AI could not answer."
    ),
    responses={200: UnansweredQuestionSerializer(many=True)},
)

stats_schema = extend_schema(
    summary="Conversation and message stats",
    description="Aggregated conversation and message counts grouped by the chosen period.",
    parameters=[
        OpenApiParameter(
            name="period",
            type=str,
            location=OpenApiParameter.QUERY,
            enum=["daily", "weekly", "monthly"],
            default="daily",
            description="Aggregation granularity.",
        ),
    ],
    responses={200: StatsSerializer(many=True)},
)
