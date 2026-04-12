from django.urls import path
from .views import notification_count, notification_list, mark_all_read

urlpatterns = [
    path("count/", notification_count, name="notification-count"),
    path("", notification_list, name="notification-list"),
    path("read/", mark_all_read, name="notification-mark-read"),
]
