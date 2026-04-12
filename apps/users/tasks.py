# Python modules
import logging
# Third party apps modules
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from settings.base import DEFAULT_FROM_EMAIL

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def send_welcome_email(self, user_id):
    User = get_user_model()

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("send_welcome_email: user %s not found", user_id)
        return

    send_mail(
        subject="Welcome!",
        message=f"Hello! {user.email}, thank you for registration!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    logger.info("Welcome email sent to %s", user.email)
