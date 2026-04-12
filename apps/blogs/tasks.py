# Python modules
import json
import logging
from datetime import timedelta
# Third party apps modules
import redis
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
# Project modules
from .models import Post, Comment
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def publish_scheduled_posts(self):
    now = timezone.now()
    due_posts = Post.objects.filter(status="scheduled", published_at__lte=now,).select_related("author")
    
    if not due_posts.exists():
        return
    
    r = redis.from_url(getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/1"))

    for post in due_posts:
        post.status = "published"
        post.published_at = now
        post.save(update_fields=["status", "published_at"])

        r.publish("post_published", json.dumps({
            "post_id": post.id, # type: ignore
            "title": post.title,
            "slug": post.slug,
            "author": {"id": post.author.id, "email": post.author.email}, # type: ignore
            "published_at": post.published_at.isoformat(), # type: ignore
        }))
        logger.info("Published scheduled post: %s (id=%s)", post.slug, post.id) # type: ignore

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def invalidate_posts_cache(self, post_id):
    cache.delete("posts_list")
    if post_id:
        cache.delete(f"post_{post_id}")
    logger.info("Cache invalidated for post_id=%s", post_id)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def generate_daily_stats(self):
    since = timezone.now() - timedelta(hours=24)

    logger.info(
        "Daily stats - posts: %d | comments: %d | users: %d",
        Post.objects.filter(created_at__gte=since).count(),
        Comment.objects.filter(created_at__gte=since).count(),
        User.objects.filter(created_at__gte=since).count(),
    )

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def clear_expired_notifications(self):
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info("Deleted %d expired notifications", deleted)
    