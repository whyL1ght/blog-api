# Django modules
from django.db.models import (
    ForeignKey,
    BooleanField,
    DateTimeField,
    Model,
    CASCADE,
)

from django.conf import settings

from apps.blogs.models import Comment


class Notification(Model):
    """
    Model for SSE
    """
    recipient = ForeignKey(settings.AUTH_USER_MODEL,
                           on_delete=CASCADE, related_name="notifications")
    comment = ForeignKey(Comment, on_delete=CASCADE,
                         related_name="notifications")
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
