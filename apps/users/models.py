# Python modules
from typing import Any
# Django modules
from django.db.models import (
    CharField,
    EmailField,
    BooleanField,
    ImageField,
    DateTimeField,
)
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom user manager for custom user
    """

    def __obtain_user_instance(
            self,
            email: str,
            first_name: str,
            last_name: str,
            password: str,
            **kwargs: dict[str, Any],
    ):
        if not email:
            raise ValidationError(message="Email field is required")
        if not first_name:
            raise ValidationError(message="First name is required")
        if not last_name:
            raise ValidationError(message="Last name is required")
        new_user: "User" = self.model(
            email=self.normalize_email(email),
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        return new_user
    
    def create_user(
            self,
            email: str,
            first_name: str,
            last_name: str,
            password: str,
            **kwargs: dict[str, Any],
    ):
        new_user = self.__obtain_user_instance(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user
    
    def create_superuser(
            self,
            email: str,
            first_name: str,
            last_name: str,
            password: str,
            **kwargs: dict[str, Any],
    ):
        new_superuser = self.__obtain_user_instance(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **{
                "is_staff": True,
                "is_superuser": True,
                **kwargs,
            },
        )
        new_superuser.set_password(password)
        new_superuser.save(using=self._db)
        return new_superuser


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email field as login
    """
    FIRST_NAME_MAX_LENGTH = 50
    LAST_NAME_MAX_LENGTH = 50
    LANGUAGE_MAX_LENGTH = 10
    TIMEZONE_MAX_LENGTH = 50
    LANGUAGE_CHOICES = [
        ("en", _("English")),
        ("ru", _("Russian")),
        ("kk", _("Kazakh")),
    ]

    email = EmailField(unique=True, verbose_name=_("Email address"))
    first_name = CharField(max_length=FIRST_NAME_MAX_LENGTH, verbose_name=_("First Name"))
    last_name = CharField(max_length=LAST_NAME_MAX_LENGTH, verbose_name=_("Last Name"))
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(default=timezone.now)
    avatar = ImageField(blank=True, null=True)
    language = CharField(
        max_length=LANGUAGE_MAX_LENGTH, choices=LANGUAGE_CHOICES, 
        default="en", verbose_name="Preferred language",
        )
    timezone = CharField(max_length=TIMEZONE_MAX_LENGTH, default="UTC", verbose_name=_("Timezone"),)

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["date_joined"]

    def __str__(self) -> str:
        return f"{self.email}"