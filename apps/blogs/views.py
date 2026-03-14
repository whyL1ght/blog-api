# Third party modules
import json
import logging
import redis
import httpx
import asyncio

# Django modules
from django.core.cache import cache
from django.contrib.auth import get_user_model
# DRF modules
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiExample, 
    extend_schema_view, 
    OpenApiParameter,
    inline_serializer,
    
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.serializers import (
    IntegerField, 
    CharField, 
    ListField, 
    DictField,
)
from rest_framework.viewsets import ModelViewSet, ViewSet
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

# Project modules
from .models import Comment, Post
from .permissions import IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostDetailSerializer, PostListSerializer
from .throttles import PostCreateThrottle


logger = logging.getLogger(__name__)
User = get_user_model()

def get_posts_cache_key(lang: str) -> str:
    return f"posts_list_{lang}"

POSTS_CACHE_TTL = 60


def _get_redis():
    return redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


@extend_schema(tags=["Posts"])
@extend_schema_view(
    list=extend_schema(
        summary="List published posts",
        description=(
            "Returns a paginated list of published posts. "
            "Not authorized users see only published posts. "
            "Authenticated users see all posts."
        ),
        parameters=[
            OpenApiParameter(
                name="lang",
                description="Language code (en, ru, kk)",
                required=False,
                type=str,
            ),
        ],
        responses={
            HTTP_200_OK: PostListSerializer(many=True),
        },
    ),
    retrieve=extend_schema(
        summary="Get a single post by slug",
        description="Returns full post details",
        responses={
            HTTP_200_OK: PostDetailSerializer,
            HTTP_404_NOT_FOUND: inline_serializer(
                name="PostNotFound",
                fields={"detail": CharField()},
            ),
        },
    ),
    create=extend_schema(
        summary="Create a new post",
        description="Creates a new post. Requires authentication.",
        request=PostDetailSerializer,
        responses={
            HTTP_201_CREATED: PostDetailSerializer,
            HTTP_400_BAD_REQUEST: inline_serializer(
                name="PostValidationError",
                fields={"title": ListField(child=CharField())},
            ),
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="PostNotAuthenticated",
                fields={"detail": CharField()},
            ),
            HTTP_429_TOO_MANY_REQUESTS: inline_serializer(
                name="PostCreateThrottle",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                "Create post",
                value={
                    "title": "My post",
                    "body": "This is the content",
                    "status": "published",
                    "category_id": 1,
                    "tag_ids": [1, 2],
                },
                request_only=True,
            ),
        ],
    ),
    partial_update=extend_schema(
        summary="Update a post",
        description="Partially updates a post. Required authentication.",
        request=PostDetailSerializer,
        responses={
            HTTP_200_OK: PostDetailSerializer,
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="PostUpdateNotAuthenticated",
                fields={"detail": CharField()},
            ),
            HTTP_403_FORBIDDEN: inline_serializer(
                name="PostUpdatePermissionDenied",
                fields={"detail": CharField()},
            ),
            HTTP_404_NOT_FOUND: inline_serializer(
                name="PostUpdateNotFound",
                fields={"detail": CharField()},
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete a post",
        description="Deletes a post. Requires authentication.",
        responses={
            HTTP_204_NO_CONTENT: None,
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="PostDeleteNotAuthenticated",
                fields={"detail": CharField()},
            ),
            HTTP_403_FORBIDDEN: inline_serializer(
                name="PostDeletePermissionDenied",
                fields={"detail": CharField()},
            ),
            HTTP_404_NOT_FOUND: inline_serializer(
                name="PostDeletionNotFound",
                fields={"detail": CharField()},
            ),
        },
    ),
    comments=extend_schema(
        summary="List or create comments",
        description=(
            "GET: Returns all comments for a post. "
            "POST: Creates a new comment. Auth required."
        ),
        request=CommentSerializer,
        responses={
            HTTP_200_OK: CommentSerializer(many=True),
            HTTP_201_CREATED: CommentSerializer,
            HTTP_401_UNAUTHORIZED: inline_serializer(
                name="CommentNotAunthenticated",
                fields={"detail": CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                "Add comment",
                value={"body": "Great post!"},
                request_only=True,
            ),
        ],
    ),
)
class PostViewSet(ModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("category", "tags")
    lookup_field = "slug"
    permission_classes = [IsOwnerOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_throttles(self):
        if self.action == "create":
            return [PostCreateThrottle()]
        return []

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ["list", "retrieve"]:
            if not self.request.user.is_authenticated:
                return qs.filter(status="published")
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        return PostDetailSerializer

    def list(self, request, *args, **kwargs):
        lang = getattr(request, "LANGUAGE_CODE", "en")
        cache_key = get_posts_cache_key(lang)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.debug("Posts list served from cache (lang=%s)", lang)
            return Response(cached_data)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            cache.set(cache_key, data, POSTS_CACHE_TTL)
            logger.debug("Posts list cached (lang=%s, ttl=%ss)", lang, POSTS_CACHE_TTL)
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(cache_key, data, POSTS_CACHE_TTL)
        logger.debug("Posts list cached (lang=%s, ttl=%ss)", lang, POSTS_CACHE_TTL)
        return Response(data)

    def perform_create(self, serializer):
        user = self.request.user
        logger.info("Post creation attempt by: %s", user.email) # type: ignore
        try:
            post = serializer.save(author=user)
            for lang_code, _ in [("en", ""), ("ru", ""), ("kk", "")]:
                cache.delete(get_posts_cache_key(lang_code))
            logger.info("Post created: '%s' (id=%s) by %s", post.title, post.pk, user.email) # type:ignore
        except Exception:
            logger.exception("Failed to create post for user: %s", user.email) # type: ignore
            raise

    def perform_update(self, serializer):
        user = self.request.user
        try:
            post = serializer.save()
            for lang_code, _ in [("en", ""), ("ru", ""), ("kk", "")]:
                cache.delete(get_posts_cache_key(lang_code))
            logger.info("Post updated: '%s' (id=%s) by %s", post.title, post.pk, user.email) # type: ignore
        except Exception:
            logger.exception("Failed to update post")
            raise

    def perform_destroy(self, instance):
        user = self.request.user
        logger.info("Post deleted: '%s' (id=%s) by %s", instance.title, instance.pk, user.email) # type: ignore
        for lang_code, _ in [("en", ""), ("ru", ""), ("kk", "")]:
            cache.delete(get_posts_cache_key(lang_code))
        instance.delete()

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
        serializer_class=CommentSerializer,
    )
    def comments(self, request, slug=None):
        post = self.get_object()

        if request.method == "GET":
            comments = post.comments.select_related("author").all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post, author=request.user)

        logger.info("Comment created (id=%s) on post '%s' by %s", comment.pk, post.slug, request.user.email)

        try:
            r = _get_redis()
            payload = json.dumps({
                "event":      "new_comment",
                "comment_id": comment.pk,
                "post_slug":  post.slug,
                "author":     request.user.email,
                "body":       comment.body,
            })
            r.publish("comments", payload)
            logger.debug("Published new_comment event to Redis channel 'comments'")
        except Exception:
            logger.exception("Failed to publish comment event")

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

@extend_schema(tags=["Stats"])
class StatsViewSet(ViewSet):
    """
    ViewSet for Stats 
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get blog statistics with external data",
        description=(
            "Returns blog statistics combined with exchange rates and current time. "
            "External API calls are made concurrently using asyncio.gather."
        ),
        responses={
            200: inline_serializer(
                name="StatsResponse",
                fields={
                    "blog": inline_serializer(
                        name="BlogStats",
                        fields={
                            "total_posts": IntegerField(),
                            "total_comments": IntegerField(),
                            "total_users": IntegerField(),
                        },
                    ),
                    "exchange_rates": DictField(),
                    "current_time": CharField(),
                },
            ),
        },
    )
    @action(detail=False, methods=["get"], url_path="")
    def stats(self, request):
        """
        We need to fetch data from 2 external APIs so because of this we need async
        """
        blog_stats = {
            "total_posts": Post.objects.count(),
            "total_comments": Comment.objects.count(),
            "total_users": User.objects.count(),
        }
        
        exchange_rates, current_time = asyncio.run(self._fetch_external_data())

        return Response(
            {
            "blog": blog_stats,
            "exchange_rates": exchange_rates,
            "current_time": current_time,
            }
        )
    async def _fetch_external_data(self):
        """
        Fetch the data from two external APIs
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            results = await asyncio.gather(
                self._fetch_exchange_rates(client), # type: ignore
                self._fetch_current_time(client), # type: ignore
                return_exceptions=True,
            )
            exchange_rates = results[0] if not isinstance(results[0], Exception) else {}
            current_time = results[1] if not isinstance(results[1], Exception) else "N/A"
            return exchange_rates, current_time
        
        async def _fetch_exchange_rates(self, client: httpx.AsyncClient):
            try:
                response = await client.get("https://open.er-api.com/v6/latest/USD")
                response.raise_for_status()
                data = response.json()

                rates = data.get("rates", {})
                return {
                    "KZT": rates.get("KZT"),
                    "RUB": rates.get("RUB"),
                    "EUR": rates.get("EUR"),
                }
            except Exception as e:
                logger.error(f"Failed to fetch exchange rates: {e}")
                return {}
            
        async def _fetch_current_time(self, client: httpx.AsyncClient):
            try:
                response = await client.get("https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty")
                response.raise_for_status()
                data = response.json()
                return data.get("dateTime", "N/A")


            except Exception as e:
                logger.error(f"Failed to fetch current time: {e}")
                return "N/A"