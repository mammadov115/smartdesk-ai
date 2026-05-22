import json
import logging
from datetime import timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _group_name(session_id: int) -> str:
    return f"chat_{session_id}"


# ──────────────────────────────────────────────────────────────────────────────
# Customer consumer  —  ws://…/ws/chat/<session_id>/
# ──────────────────────────────────────────────────────────────────────────────


class CustomerConsumer(AsyncWebsocketConsumer):
    """
    WebSocket endpoint for the customer-facing chat widget.

    Lifecycle:
      • connect  — authenticate via JWT (set by JWTAuthMiddleware), verify
                   the session belongs to this user, join the channel group.
      • receive  — forward customer messages to the group when session is LIVE.
                   Messages sent while the AI is still handling things are
                   ignored (the REST /ask/ endpoint handles that flow).
      • disconnect — leave the group.

    Group events:
      • chat.message — broadcast any message (operator or system) to the socket.
    """

    async def connect(self):
        self.session_id = int(self.scope["url_route"]["kwargs"]["session_id"])
        self.group_name = _group_name(self.session_id)

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        session = await _get_customer_session(self.session_id, user)
        if session is None:
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("CustomerConsumer connected: session=%s user=%s", self.session_id, user.pk)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        content = (data.get("message") or "").strip()
        if not content:
            return

        user = self.scope["user"]
        session = await _get_customer_session(self.session_id, user)
        if session is None or session.status != ChatSession.Status.LIVE:
            # Only allow live messages when an operator has joined
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "detail": "No operator is available yet.",
                    }
                )
            )
            return

        msg = await _save_message(session, ChatMessage.Role.USER, content)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message_id": msg.id,
                "role": ChatMessage.Role.USER,
                "content": content,
                "created_at": msg.created_at.isoformat(),
            },
        )

    # ── channel layer event handlers ──────────────────────────────────────────

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message_id": event["message_id"],
                    "role": event["role"],
                    "content": event["content"],
                    "created_at": event["created_at"],
                }
            )
        )


# ──────────────────────────────────────────────────────────────────────────────
# Operator consumer  —  ws://…/ws/operator/chat/<session_id>/
# ──────────────────────────────────────────────────────────────────────────────


class OperatorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket endpoint for the operator dashboard.

    Lifecycle:
      • connect  — authenticate (staff user only), look up the session,
                   claim it (status → LIVE, operator = this user), join:
                     - the per-session group  chat_<id>   (live chat)
                     - the global group       operators_room  (escalation alerts)
      • receive  — broadcast operator messages to the session group.
      • disconnect — leave both groups; if no other operator is present the
                     session reverts to WAITING so another operator can pick it up.

    Group events:
      • chat.message           — live message in this session.
      • escalation.notification — a different session needs attention
                                  (sent by escalate_to_operator service).
    """

    async def connect(self):
        self.session_id = int(self.scope["url_route"]["kwargs"]["session_id"])
        self.group_name = _group_name(self.session_id)

        user = self.scope.get("user")
        if not user or not user.is_authenticated or not user.is_staff:
            await self.close(code=4001)
            return

        session = await _get_operator_session(self.session_id)
        if session is None:
            await self.close(code=4004)
            return

        # Claim the session
        await _assign_operator(session, user)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.channel_layer.group_add("operators_room", self.channel_name)
        await self.accept()

        logger.debug("OperatorConsumer connected: session=%s operator=%s", self.session_id, user.pk)

        # Notify the customer that an operator has joined
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message_id": None,
                "role": "system",
                "content": "An operator has joined the conversation.",
                "created_at": _now_iso(),
            },
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_discard("operators_room", self.channel_name)

        # Revert to WAITING so another operator can pick it up
        session = await _get_operator_session(self.session_id)
        if session and session.status == ChatSession.Status.LIVE:
            await _release_session(session)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        content = (data.get("message") or "").strip()
        if not content:
            return

        session = await _get_operator_session(self.session_id)
        if session is None:
            return

        msg = await _save_message(session, ChatMessage.Role.OPERATOR, content)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message_id": msg.id,
                "role": ChatMessage.Role.OPERATOR,
                "content": content,
                "created_at": msg.created_at.isoformat(),
            },
        )

    # ── channel layer event handlers ──────────────────────────────────────────

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message_id": event["message_id"],
                    "role": event["role"],
                    "content": event["content"],
                    "created_at": event["created_at"],
                }
            )
        )

    async def escalation_notification(self, event):
        """Notify this operator that another session needs attention."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "escalation",
                    "session_id": event["session_id"],
                    "owner_email": event["owner_email"],
                }
            )
        )


# ──────────────────────────────────────────────────────────────────────────────
# DB helpers (run in thread pool via database_sync_to_async)
# ──────────────────────────────────────────────────────────────────────────────


@database_sync_to_async
def _get_customer_session(session_id: int, user):
    try:
        return ChatSession.objects.get(pk=session_id, owner=user)
    except ChatSession.DoesNotExist:
        return None


@database_sync_to_async
def _get_operator_session(session_id: int):
    try:
        return ChatSession.objects.get(pk=session_id)
    except ChatSession.DoesNotExist:
        return None


@database_sync_to_async
def _assign_operator(session: ChatSession, user):
    session.operator = user
    session.status = ChatSession.Status.LIVE
    session.save(update_fields=["operator", "status", "updated_at"])


@database_sync_to_async
def _release_session(session: ChatSession):
    session.operator = None
    session.status = ChatSession.Status.WAITING
    session.save(update_fields=["operator", "status", "updated_at"])


@database_sync_to_async
def _save_message(session: ChatSession, role: str, content: str) -> ChatMessage:
    return ChatMessage.objects.create(session=session, role=role, content=content)


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now(tz=timezone.utc).isoformat()
