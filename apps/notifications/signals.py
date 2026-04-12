import json
# Third party apps
import redis
# Django modules
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
# Project modules
from .models import Notification
from apps.blogs.tasks import invalidate_posts_cache
from .tasks import process_new_comment


@receiver(post_save, sender="blogs.Comment")
def on_comment_created(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(lambda: process_new_comment.delay(comment_id=instance.id)) # type: ignore


@receiver(post_save, sender="blogs.Post")
def on_post_published(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: invalidate_posts_cache.delay(
        post_id=instance.id))  # type: ignore

    if instance.status != "published":
        return

    update_fields = kwargs.get("update_fields")
    if not created and update_fields and "status" not in update_fields:
        return

    r = redis.from_url(getattr(settings, "REDIS_URL",
                       "redis://127.0.0.1:6379/0"))

    data = json.dumps({
        "post_id": instance.id,
        "title": instance.title,
        "slug": instance.slug,
        "author": {"id": instance.author.id, "email": instance.author.email},
        "published_at": instance.published_at.isoformat() if instance.published_at else None,
    })
    r.publish("post_published", data)
