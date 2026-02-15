# Python modules
from tabnanny import verbose
from typing import Any
# Django modules
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils import timezone


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
    FIRST_NAME_MAX_LENGHT = 50
    LAST_NAME_MAX_LENGHT = 50

    email = models.EmailField(unique=True, verbose_name="Email address")
    first_name = models.CharField(max_length=FIRST_NAME_MAX_LENGHT, verbose_name="First Name")
    last_name = models.CharField(max_length=LAST_NAME_MAX_LENGHT, verbose_name="Last Name")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.email}"