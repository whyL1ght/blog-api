# Django modules
from django.db.models import (
    CharField,
    SlugField,
    TextField,
    ForeignKey,
    ManyToManyField,
    DateTimeField,
    SET_NULL,
    CASCADE,
    Model,
)
# Project modules
from apps.users.models import User


NAME_MAX_LENGHT = 100
TITLE_MAX_LENGHT = 200
STATUS_MAX_LENGHT = 30


class Category(Model):
    """
    Model for category in db
    """

    name = CharField(max_length=NAME_MAX_LENGHT, unique=True)
    slug = SlugField(unique=True)

    class Meta:
        verbose_name = "Category"


class Tag(Model):
    """
    Model for Tag in db
    """
    
    name = CharField(max_length=NAME_MAX_LENGHT, unique=True)
    slug = SlugField(unique=True)

    class Meta:
        verbose_name = "Tag"


class Post(Model):
    """
    Model for Post in db
    """

    STATUS_CHOICE = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    author = ForeignKey(User, on_delete=CASCADE)
    title = CharField(max_length=TITLE_MAX_LENGHT)
    slug = SlugField(unique=True)
    body = TextField()
    category_id = ForeignKey(Category, on_delete=SET_NULL, null=True)
    tags = ManyToManyField(Tag, blank=True)
    status = CharField(max_length=STATUS_MAX_LENGHT,choices=STATUS_CHOICE)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Post"


class Comment(Model):
    """
    Model for comment in db
    """    

    post = ForeignKey(Post, on_delete=CASCADE)
    author = ForeignKey(User, on_delete=CASCADE)
    body = TextField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comment"


