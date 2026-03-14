# Third party modules
import logging
# DRF, rest modules
from rest_framework.serializers import CharField
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from rest_framework.status import (
    HTTP_201_CREATED, 
    HTTP_400_BAD_REQUEST,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_403_FORBIDDEN,
    HTTP_204_NO_CONTENT,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# project modules
from apps.blogs.throttles import LoginTareThrottle


logger = logging.getLogger(__name__)


class LoggedTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginTareThrottle]

    @extend_schema(
        tags=["Auth"],
        summary="Obtain JWT token pair",
        description=(
            "Authenticates a user with email and password. "
            "Returns access and refresh tokens. "
            "Rate limit: 10 requests per minute per IP."
        ),
        responses={
            HTTP_200_OK: inline_serializer(
                name="TokenPairResponse",
                fields={
                    "refresh": CharField(),
                    "access": CharField(),
                },
            ),
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="InvalidCredentials",
                fields={"detail": CharField()},
            ),
            HTTP_429_TOO_MANY_REQUESTS: inline_serializer(
                name="LoginThrottled",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                "Login",
                value={"email": "user@example.com", "password": "securepass123"},
                request_only=True,
            ),
            OpenApiExample(
                "Success",
                value={
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "-")
        logger.info("Login attempt for email : %s", email)
        response = super().post(request, *args, **kwargs)

        if response.status_code == HTTP_200_OK:
            logger.info("Login successful for email: %s", email)
        else:
            logger.warning("Login failed for email: %s", email)
        return response
    

class LoggedTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Auth"],
        summary="Refresh JWT access token",
        description="Exchanges a refresh token for a new access token.",
        responses={
            HTTP_200_OK: inline_serializer(
                name="RefreshTokenResponse",
                fields={"access": CharField()},
            ),
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="InvalidRefreshToken",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                "Refresh token",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."},
                request_only=True,
            ),
            OpenApiExample(
                "Success",
                value={"access": "eyJ0eXAiOiJKV1QiLCJhbGc..."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        logger.debug("Token refresh requested")
        return super().post(request, *args, **kwargs)
