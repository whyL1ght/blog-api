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
from django.utils.translation import get_language, gettext_lazy as _
# Project modules
from apps.users.models import User


NAME_MAX_LENGTH = 100
TITLE_MAX_LENGTH = 200
STATUS_MAX_LENGTH = 30


class Category(Model):
    """
    Model for category in db
    """

    name = CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = SlugField(unique=True, verbose_name=_("Slug"))

    class Meta:
        verbose_name = _("Category")

    def __str__(self):
        return self.get_name()
    
    def get_name(self, lang=None):
        if lang is None:
            lang = get_language()
    
        translation = self.translations.filter(language=lang).first()  # type: ignore
        if translation:
            return translation.name
        
        fallback = self.translations.filter(language="en").first()  # type: ignore
        return fallback.name if fallback else f"Category {self.id}"
    

class CategoryTranslation(Model):
    """
    Model for CategoryTranslation
    """
    NAME_MAX_LENGTH = 100
    LANGUAGE_MAX_LENGTH = 10

    category = ForeignKey(
        Category,
        on_delete=CASCADE,
        related_name="translations",
    )
    language = CharField(
        max_length=LANGUAGE_MAX_LENGTH,
        choices=[("en", "English"), ("ru", "Russian"), ("kk", "Kazakh")],
    )
    name = CharField(max_length=NAME_MAX_LENGTH, verbose_name=_("Title"))
 
    class Meta:
        unique_together = [("category", "language")]
        verbose_name = _("Category Translation")
        verbose_name_plural = _("Category Translations")
 
    def __str__(self) -> str:
        return f"{self.category.slug} [{self.language}]: {self.name}"


class Tag(Model):
    """
    Model for Tag in db
    """
    
    name = CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = SlugField(unique=True)

    class Meta:
        verbose_name = _("Tag")


class Post(Model):
    """
    Model for Post in db
    """

    STATUS_CHOICE = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    author = ForeignKey(User, on_delete=CASCADE)
    title = CharField(max_length=TITLE_MAX_LENGTH)
    slug = SlugField(unique=True)
    body = TextField()
    category_id = ForeignKey(Category, on_delete=SET_NULL, null=True)
    tags = ManyToManyField(Tag, blank=True)
    status = CharField(max_length=STATUS_MAX_LENGTH,choices=STATUS_CHOICE)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Post")


class Comment(Model):
    """
    Model for comment in db
    """    

    post = ForeignKey(Post, on_delete=CASCADE)
    author = ForeignKey(User, on_delete=CASCADE)
    body = TextField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Comment")


