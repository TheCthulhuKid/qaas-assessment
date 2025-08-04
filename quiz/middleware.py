from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware for maintaining authentication while using websockets
    """
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token_param = None

        if query_string:
            params = query_string.split("&")
            for param in params:
                if param.startswith("token="):
                    token_param = param.split("=")[1]
                    break

        if token_param:
            scope["user"] = await get_user(token_param)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
