# Thrid party modules
import logging
import redis
import json
# DRF modules
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_201_CREATED
# Django modules
from django.shortcuts import render
from django.core.cache import cache
from apps.blogs import serializers
from apps.blogs.throttles import PostCreateThrottle
# Project modules
from .models import Comment, Post
from apps.blogs.permissions import IsOwnerOrReadOnly
from apps.blogs.serializers import CommentSerializer, PostDetailSerialize, PostListSerializer


logger = logging.getLogger(__name__)
POSTS_CACHE_KEY = "posts_list"
POSTS_CACHE_TTL = 60


class PostViewSet(ModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("category","tags")
    lookup_field = "slug"
    permission_classes = [IsOwnerOrReadOnly]


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
        return PostDetailSerialize
    

    def list(self, request, *args, **kwargs):
        cached_data = cache.get(POSTS_CACHE_KEY)
        if cached_data is not None:
            logger.debug("Post list served from cache")
            return Response(cached_data)
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            cache.set(POSTS_CACHE_KEY, data, POSTS_CACHE_TTL)
            logger.debug("Posts list written to cache (%ss TTL)", POSTS_CACHE_TTL)
            return self.get_paginated_response(data)
        
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(POSTS_CACHE_KEY, data, POSTS_CACHE_TTL)
        logger.debug("Posts list written to cache (%ss TTL)", POSTS_CACHE_TTL)
        return Response(data)

    

    def perform_create(self, serializer):
        user = self.request.user
        logger.info("Post creation attempt by: %s", user.email)
        try:
            post = serializer.save(author=user)
            cache.delete(POSTS_CACHE_KEY)
            logger.info("Post creation attempt by: %s", user.email)
        except Exception:
            logger.exception("Failed to create post for user: %s", user.email)
            raise


    def perform_update(self, serializer):
        user = self.request.user
        try:
            post = serializer.save(author=user)
            cache.delete(POSTS_CACHE_KEY)
            logger.info("Post updated: '%s' (id=%s) by %s", post.title, post.pk, user.email)
        except Exception:
            logger.exception("Failed to update post")
            raise


    def perform_destroy(self, instance):
        user = self.request.user
        logger.info("Post deleted: '%s' (id=%s) by %s", instance.title, instance.pk, user.email)
        cache.delete(POSTS_CACHE_KEY)
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
            serializer = CommentSerializer(comments,many=True)
            return Response(serializer.data)
        
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=HTTP_401_UNAUTHORIZED
            )
        
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logger.info(
            "Comment created (id=%s) on post '%s' by %s",
            comment.pk, post.slug, request.user.email,
        )
        try:
            r = _get_redis()
            payload = json.dumps({
                "event": "new_comment",
                "comment_id": comment.pk,
                "post_slug": post_slug,
                "author": request.user.email,
                "body": comment.body,
            })
            r.publish("comments", payload)
            logger.degub("Published new_comment event to redis channel 'comments'")
        except Exception:
            logger.exception("Failed to published comment")
        return Response(serializer.data, status=HTTP_201_CREATED)