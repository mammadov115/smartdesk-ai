from django.db.models import Count, Max, Min
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek

from apps.chat.models import ChatMessage, ChatSession

from .utils import cluster_by_cosine_similarity

_TRUNC = {
    "daily": TruncDay,
    "weekly": TruncWeek,
    "monthly": TruncMonth,
}

_TOP_CLUSTERS = 10


def get_conversations(user) -> list[dict]:
    """Return all sessions for *user* with basic aggregate metadata."""
    sessions = (
        ChatSession.objects.filter(owner=user)
        .annotate(
            message_count=Count("messages"),
            first_message_at=Min("messages__created_at"),
            last_message_at=Max("messages__created_at"),
        )
        .order_by("-created_at")
    )

    data = []
    for s in sessions:
        duration = None
        if s.first_message_at and s.last_message_at and s.first_message_at != s.last_message_at:
            duration = int((s.last_message_at - s.first_message_at).total_seconds())
        data.append(
            {
                "id": s.id,
                "status": s.status,
                "created_at": s.created_at,
                "message_count": s.message_count,
                "first_message_at": s.first_message_at,
                "last_message_at": s.last_message_at,
                "duration_seconds": duration,
            }
        )
    return data


def get_conversation_detail(user, pk: int) -> dict:
    """
    Return session metadata and full message history.

    Raises:
        ChatSession.DoesNotExist: if the session does not belong to *user*.
    """
    session = ChatSession.objects.get(pk=pk, owner=user)
    messages = list(session.messages.order_by("created_at").values("id", "role", "content", "sources", "created_at"))
    return {
        "id": session.id,
        "status": session.status,
        "created_at": session.created_at,
        "message_count": len(messages),
        "messages": messages,
    }


def get_most_asked_questions(user, top_n: int = _TOP_CLUSTERS) -> list[dict]:
    """
    Cluster semantically similar user questions and return the most frequent ones.

    Only messages that have a stored embedding are considered.  Questions asked
    before the embedding field was introduced are silently skipped.
    """
    msgs = list(
        ChatMessage.objects.filter(
            session__owner=user,
            role=ChatMessage.Role.USER,
            embedding__isnull=False,
        ).values("id", "content", "embedding")
    )

    if not msgs:
        return []

    clusters = cluster_by_cosine_similarity(msgs)
    return [{"question": msgs[c[0]]["content"], "count": len(c)} for c in clusters[:top_n]]


def get_unanswered_questions(user) -> list[dict]:
    """
    Return the last user question from each session that was escalated to an
    operator (status WAITING or LIVE) — i.e. questions the AI could not answer.
    """
    escalated = ChatSession.objects.filter(
        owner=user,
        status__in=[ChatSession.Status.WAITING, ChatSession.Status.LIVE],
    )
    # DISTINCT ON (session_id) + ORDER BY session_id, -created_at →
    # latest user message per session.  PostgreSQL-specific but fine since
    # the whole project targets PostgreSQL.
    msgs = (
        ChatMessage.objects.filter(
            session__in=escalated,
            role=ChatMessage.Role.USER,
        )
        .select_related("session")
        .order_by("session_id", "-created_at")
        .distinct("session_id")
    )
    return [
        {
            "session_id": m.session_id,
            "question": m.content,
            "asked_at": m.created_at,
            "session_created_at": m.session.created_at,
        }
        for m in msgs
    ]


def get_stats(user, period: str = "daily") -> list[dict]:
    """
    Return conversation and message counts grouped by *period*.

    *period* must be one of ``"daily"``, ``"weekly"``, or ``"monthly"``.
    Defaults to ``"daily"`` for any unrecognised value.
    """
    trunc_fn = _TRUNC.get(period, TruncDay)
    return list(
        ChatSession.objects.filter(owner=user)
        .annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(
            conversations=Count("id", distinct=True),
            messages=Count("messages"),
        )
        .order_by("-period")
    )
