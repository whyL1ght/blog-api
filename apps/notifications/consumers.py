import json

# Third party apps modules
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
# Project modules
from apps.blogs.models import Post


User = get_user_model()


class CommentConsumer(AsyncWebsocketConsumer):
    """
    Websocket Consumer
    """

    async def connect(self):
        slug = self.scope["url_route"]["kwargs"]["slug"]   # type: ignore

        user = await self._authenticate()
        if user is None:
            await self.scope(code=4001)   # type: ignore
            return

        post_exists = await self._post_exists(slug)
        if not post_exists:
            await self.close(code=4004)
            return

        self.slug = slug
        self.group_name = f"post_comments_{slug}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def new_comment(self, event):
        await self.send(text_data=json.dumps({
            "comment_id": event["comment_id"],
            "author": event["author"],
            "body": event["body"],
            "created_at": event["created_at"],
        }))

    async def _authenticate(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = dict(
            part.split("=", 1)
            for part in query_string.split("&")
            if "=" in part
        )
        raw_token = params.get("token")
        if not raw_token:
            return None
        try:
            validated = AccessToken(raw_token)  # type: ignore
            user_id = validated["user_id"]
            return await self._get_user(user_id)
        except (TokenError, InvalidToken, KeyError):
            return None

    @database_sync_to_async
    def _get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _post_exists(self, slug):
        return Post.objects.filter(slug=slug).exists()
