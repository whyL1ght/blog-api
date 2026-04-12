# Third party modules
from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    CharField,
    EmailField,
)
# Project modules
from .models import Notification


class NotificationSerializer(ModelSerializer):
    """
    Serializer for Notification model
    """
    comment_id = IntegerField(source="comment.id", read_only=True)
    post_slug = CharField(source="comment.post.slug", read_only=True)
    comment_body = CharField(source="comment.body", read_only=True)
    commenter_email = EmailField(source="comment.author.email", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "comment_id", "post_slug", "comment_body",
                  "commenter_email", "is_read", "created_at"]
