# DRF modules
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
# Django modules
from django.contrib import admin
from django.urls import path, include
# Project modules
from apps.users.views import RegisterViewSet, UserPreferencesViewSet
from apps.users.token_views import LoggedTokenObtainPairView, LoggedTokenRefreshView
router = DefaultRouter()

router.register(r"register", RegisterViewSet, basename="register")
router.register(r"", UserPreferencesViewSet, basename="user-pref")

urlpatterns = [
    path("api/auth/", include(router.urls)),
    path("api/auth/token/", LoggedTokenObtainPairView.as_view()),
    path("api/auth/token/refresh", LoggedTokenRefreshView.as_view()),
]
