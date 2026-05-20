from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def _get_user_from_token(raw_token: str):
    """
    Validate a JWT access token and return the corresponding User.
    Returns AnonymousUser on any failure so the consumer can close cleanly.
    """
    try:
        token = AccessToken(raw_token)
        return User.objects.get(pk=token["user_id"])
    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Reads a JWT token from the WebSocket query string (?token=<access_token>)
    and populates scope["user"].  Keeps unauthenticated connections as
    AnonymousUser — the individual consumers decide whether to reject them.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])
        if token_list:
            scope["user"] = await _get_user_from_token(token_list[0])
        else:
            scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)
