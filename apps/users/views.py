import logging
# DRF modules
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.serializers import CharField, ListField
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import CharField, ListField
from rest_framework.status import (
    HTTP_201_CREATED, 
    HTTP_400_BAD_REQUEST,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    )
from rest_framework.decorators import action
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiExample, 
    extend_schema_view, 
    inline_serializer,
)
# Django modules
from django.shortcuts import render

from apps.blogs.throttles import RegisterRateThrottle
# Project modules
from .serializers import (
    RegisterSerializer, 
    UserSerializer,
    LanguageUpdateSerializer,
    TimezoneUpdateSerializer,
)
from .emails import send_welcome_email

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@extend_schema(tags=["Auth"])
class RegisterViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterRateThrottle]


    @extend_schema(
        summary="Register a new user",
        description=(
            "Creates a new user account and sends a welcome email in the user's language"
            "Returns user data and JWT tokens"
            "Rate limit: 5 requests per minute per IP"
        ),
        responses={
            HTTP_201_CREATED: inline_serializer(
                name="RegisterResponse",
                fields={
                    "user": UserSerializer(),
                    "tokens": inline_serializer(
                        name="TokenPair",
                        fields={
                            "refresh": CharField(),
                            "access": CharField(),
                        },
                    ),
                },
            ),
            HTTP_400_BAD_REQUEST: inline_serializer(
                name="RegisterValidationError",
                fields={"password": ListField(child=CharField())},
            ),
            HTTP_429_TOO_MANY_REQUESTS: inline_serializer(
                name="ThrottledError",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                "Register user",
                value={
                    "email": "user@example.com",
                    "first_name": "User",
                    "last_name": "Example",
                    "password": "securepass123",
                    "password2": "securepass123",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Success response",
                value={
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "User",
                        "last_name": "Example",
                        "language": "en",
                        "timezone": "UTC",
                    },
                    "tokens": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    },
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "Validation error",
                value={"password": ["Passwords don't match"]},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
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

        try:
            send_welcome_email(user)
            logger.info("Welcome email sent to: %s (lang=%s)", user.email, user.pk)
        except Exception:
            logger.exception("Failed to send welcome email to: %s", user.email)
        
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": get_tokens_for_user(user),
            },
            status=HTTP_201_CREATED,
        )
    

@extend_schema(tags=["Auth"])
class UserPreferencesViewSet(ViewSet):
    """
    ViewSet for UserPreferences
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LanguageUpdateSerializer

    @extend_schema(
        summary="Update user language preference",
        description=(
            "Updates the authenticated user's preferred language"
            "Valid values: en, ru, kk "
            "Requires authentication"
        ),
        request=LanguageUpdateSerializer,
        responses={
            HTTP_200_OK: inline_serializer(
                name="LanguageResponse",
                fields={"language": CharField()},
            ),
            HTTP_400_BAD_REQUEST: inline_serializer(
                name="LanguageValidationError",
                fields={"language": ListField(child=CharField())},
            ),
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="NotAuthenticatedError",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample("Set English", value={"language": "en"}, request_only=True),
            OpenApiExample(
                "Success",
                value={"language": "en"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=False, methods=["patch"], url_path="language")
    def update_language(self, request):
        serializer = LanguageUpdateSerializer(
            instance=request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Language updated to '%s' for user: %s", user.language, user.email) # type: ignore
        return Response({"language": user.language}) # type: ignore
    
    
    @extend_schema(
        summary="Update user timezone",
        description=(
            "Updates the authenticated user's timezone"
            "Must be a valid IANA timezone (e.g., 'Asia/Almaty')"
            "Requires authentication"
        ),
        request=TimezoneUpdateSerializer,
        responses={
            HTTP_200_OK: inline_serializer(
                name="TimezoneResponse",
                fields={"timezone": CharField()},
            ),
            HTTP_400_BAD_REQUEST: inline_serializer(
                name="TimezoneValidationError",
                fields={"timezone": ListField(child=CharField())},
            ),
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="NotAuthenticatedError2",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample("Set Almaty timezone", value={"timezone": "Asia/Almaty"}, request_only=True),
            OpenApiExample(
                "Success",
                value={"timezone": "Asia/Almaty"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=False, methods=["patch"], url_path="timezone")
    def update_timezone(self, request):
        serializer = TimezoneUpdateSerializer(
            instance=request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Timezone updated to '%s' for user: '%s'", user.timezone, user.email) # type: ignore
        return Response({"timezone": user.timezone})    # type: ignore
    



        
