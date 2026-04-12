# Python modules
import logging
# Third party apps modules
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
# Project modules
from .models import Notification
from apps.blogs.models import Comment


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def process_new_comment(self, comment_id):
    try:
        comment = Comment.objects.select_related(
            "author", "post", "post__author",
        )
    except Comment.DoesNotExist:
        logger.warning("process_new_comment: comment %s not found", comment_id)
        return

    post = comment.post  # type: ignore

    if post.author != comment.author:  # type: ignore
        _, created = Notification.objects.get_or_create(
            recipient=post.author,
            comment=comment,
        )
        if created:
            logger.info("Notification created for user %s", post.author)

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"post_comments_{post.slug}",
        {
            "type": "new_comment",
            "comment_id": comment_id,
            "author": {"id": comment.author.id, "email": comment.author.email},             # type: ignore
            "body": comment.body,  # type: ignore
            "created_at": comment.created_at.isoformat(), # type: ignore
        }
    )
