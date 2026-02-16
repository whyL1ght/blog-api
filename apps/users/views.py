import logging
# DRF modules
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
# Django modules
from django.shortcuts import render
# Project modules
from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get("email", "-")
        logger.info("Registration attempt for email: %s", email)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                "Registration failed for email: %s - errors: %s",
                email, serializer.errors,
            )
            return Response(serializer.errrors,status=HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        logger.info("User successfully registered: %s (id=%s)", user.email, user.pk)
        
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": get_tokens_for_user(user),
            },
            status=HTTP_201_CREATED,
        )