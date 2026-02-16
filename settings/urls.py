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
from apps.users.views import RegisterViewSet
from apps.blogs.views import PostViewSet

router = DefaultRouter()

router.register(r"auth/register", RegisterViewSet, basename="register")
router.register(r"posts", PostViewSet, basename="post")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
