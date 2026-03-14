# DRF modules
from rest_framework.routers import DefaultRouter
# Django modules
from django.contrib import admin
from django.urls import path, include
# Project modules
from apps.blogs.views import PostViewSet, StatsViewSet

router = DefaultRouter()

router.register(r"posts", PostViewSet, basename="post")
router.register(r"stats", StatsViewSet, basename="stats")

urlpatterns = [
    path("", include(router.urls)),
    
    ]
