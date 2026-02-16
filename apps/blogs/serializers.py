# DRF modules
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
# Project modules
from .models import (
    Category,
    Tag,
    Post,
    Comment,
)
from apps.users.serializers import UserSerializer


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


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

    class Meta:
        model = Post
        fields = ["id", "author", "category", "tags", "title", "slug", 
                  "status", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "slug", "author", "created_at", "updated_at"]


class PostDetailSerialize(ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

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
                  "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "author", "created_at", "updated_at"]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        return post
    
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        return instance

