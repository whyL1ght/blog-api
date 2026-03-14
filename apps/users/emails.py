from typing import TYPE_CHECKING
# Django modules
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation

# Project modules
if TYPE_CHECKING:
    from .models import User


def send_welcome_email(user):
    with translation.override(user.language):
        template_name = f"welcome_{user.language}.html"
        html_content = render_to_string(template_name, {"user": user})
        subject_map = {
            "en": "Welcome to my blog!",
            "kk": "Менің блогыма қош келдіңіз!",
            "ru": "Добро пожаловать в мой блог!",
        }
        subject = subject_map.get(user.language, "Welcome!")

        send_mail(
            subject=subject,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )