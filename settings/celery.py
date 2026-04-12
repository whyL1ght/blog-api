import os
# Third party modules
from celery import Celery
from celery.schedules import crontab
# Project modules
from settings.conf import ENV_ID


os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')

app = Celery("blog")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


app.conf.beat_schedule = {
    "publish_scheduled_posts": {
        "task": "apps.blogs.tasks.publish_scheduled_posts",
        "schedule": 60.0,
    },
    "clear_expired_notifications": {
        "task": "apps.blogs.tasks.clear_expired_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
    "generate_daily_stats": {
        "task": "apps.blogs.tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
    },
}