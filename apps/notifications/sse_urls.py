# Django modules
from django.urls import path
# Project modules
from .views import post_publication_stream

urlpatterns = [
    path("", post_publication_stream, name="post-stream"),
]
