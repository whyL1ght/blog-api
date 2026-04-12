import asyncio
# Third party apps
import redis.asyncio as aioredis
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
# Django modules
from django.conf import settings
from django.http import StreamingHttpResponse
# Project modules
from .models import Notification
from .serializers import NotificationSerializer


async def post_publication_stream(request):
    async def event_generator():
        redis_url = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
        redis = aioredis.from_url(redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe("post_published")
        try:
            yield ": heartbeat\n\n"
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield f"event: post_published\ndata: {data}\n\n"
                await asyncio.sleep(0)
        finally:
            await pubsub.unsubscribe("post_published")
            await redis.aclose()

    response = StreamingHttpResponse(
        event_generator(), content_type="text/event-stream")  # type: ignore
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_count(request):
    count = Notification.objects.filter(
        recipient=request.user, is_read=False).count()
    return Response({"unread count": count})


class NotificationPagination(PageNumberPagination):
    page_size = 20


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related("comment", "comment__author", "comment__post")
    paginator = NotificationPagination()
    page = paginator.paginate_queryset(notifications, request)
    serializer = NotificationSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    updated = Notification.objects.filter(
        recepient=request.user, is_read=False).update(is_read=True)
    return Response({"marked_read": updated})
