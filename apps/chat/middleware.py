from urllib.parse import parse_qs, urlparse

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
    except InvalidToken, TokenError, User.DoesNotExist, KeyError:
        return AnonymousUser()


@database_sync_to_async
def _get_owner_if_origin_allowed(embed_token: str, origin_host: str):
    """
    Return the company owner User if origin_host is in the AllowedDomain list
    for the company identified by embed_token.  Returns None otherwise.
    """
    from apps.accounts.models import AllowedDomain, CompanyProfile

    try:
        company = CompanyProfile.objects.select_related("owner").get(embed_token=embed_token)
    except CompanyProfile.DoesNotExist:
        return None
    if not AllowedDomain.objects.filter(company=company, domain=origin_host).exists():
        return None
    return company.owner


def _extract_origin_host(scope) -> str:
    """Return the bare hostname from the WS connection's Origin header."""
    headers = dict(scope.get("headers", []))
    origin = headers.get(b"origin", b"").decode()
    if not origin:
        return ""
    return urlparse(origin).hostname or ""


class JWTAuthMiddleware(BaseMiddleware):
    """
    1. Reads a JWT token from ?token=<access_token> and populates scope["user"].
    2. If ?embed_token=<uuid> is present instead, validates the Origin header
       against the company's AllowedDomain list and rejects with 403 if not found.
    """

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "websocket":
            query_string = scope.get("query_string", b"").decode()
            params = parse_qs(query_string)

            embed_token_list = params.get("embed_token", [])
            if embed_token_list:
                origin_host = _extract_origin_host(scope)
                owner = await _get_owner_if_origin_allowed(embed_token_list[0], origin_host)
                if owner is None:
                    await send({"type": "websocket.close"})
                    return
                scope["user"] = owner
                return await super().__call__(scope, receive, send)

            token_list = params.get("token", [])
            scope["user"] = await _get_user_from_token(token_list[0]) if token_list else AnonymousUser()

        return await super().__call__(scope, receive, send)
