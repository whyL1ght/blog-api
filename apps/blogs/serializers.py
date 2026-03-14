# Django modules
from django.utils.timezone import localtime
from django.utils.formats import date_format
# DRF modules
from rest_framework.serializers import (
    ModelSerializer, 
    PrimaryKeyRelatedField, 
    SerializerMethodField,
)
# Project modules
from .models import (
    Category,
    Tag,
    Post,
    Comment,
)
from apps.users.serializers import UserSerializer


class CategorySerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

    def get_name(self, obj: Category) -> str:
        return obj.get_name()


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CommentSerializer(ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "body", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class PostListSerializer(ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    created_at_formatted = SerializerMethodField()
    updated_at_formatted = SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "author", "category", "tags", "title", "slug", 
                  "status", "created_at", "updated_at", "created_at_formatted",
                  "updated_at_formatted",
        ]
        read_only_fields = [
            "id", "slug", "author", "created_at", "updated_at", 
            "created_at_formatted","updated_at_formatted",]

    def get_created_at_formatted(self, obj: Post) -> str:
        local_dt = localtime(obj.created_at)
        return date_format(local_dt, "DATETIME_FORMAT")
 
    def get_updated_at_formatted(self, obj: Post) -> str:
        local_dt = localtime(obj.updated_at)
        return date_format(local_dt, "DATETIME_FORMAT")


class PostDetailSerializer(ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    created_at_formatted = SerializerMethodField()
    updated_at_formatted = SerializerMethodField()

    category_id = PrimaryKeyRelatedField(
        queryset = Category.objects.all(),
        source = "category",
        write_only = True,
        required = False,
        allow_null = True,
    )
    tag_ids = PrimaryKeyRelatedField(
        queryset = Tag.objects.all(),
        source = "tags",
        write_only = True,
        required = True,
        allow_null = True,
    )

    class Meta:
        model = Post
        fields = ["id", "author", "category", "category_id", "tags", 
                  "tag_ids", "title", "slug", "body", "status",
                  "created_at", "updated_at", "created_at_formatted",
                  "updated_at_formatted",

        ]
        read_only_fields = [
            "id", "slug", "author", "created_at", "updated_at",
            "created_at_formatted", "updated_at_formatted",
            ]

    def get_created_at_formatted(self, obj: "Post") -> str:
        local_dt = localtime(obj.created_at)
        return date_format(local_dt, "DATETIME_FORMAT")

    def get_updated_at_formatted(self, obj: "Post") -> str: 
        local_dt = localtime(obj.updated_at)
        return date_format(local_dt, "DATETIME_FORMAT")

