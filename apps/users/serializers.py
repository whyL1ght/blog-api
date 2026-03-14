import logging
import pytz
# DRF modules
from rest_framework.serializers import (
    ModelSerializer, 
    CharField, 
    ValidationError, 
    Serializer,
    ChoiceField,
)
# Django modules
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()
logger = logging.getLogger(__name__)


PASSWORD_MIN_LENGTH = 8

class RegisterSerializer(ModelSerializer):
    """
    Serializer for registration
    """
    password = CharField(write_only = True, min_length = PASSWORD_MIN_LENGTH)
    password2 = CharField(write_only = True, min_length = PASSWORD_MIN_LENGTH)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "password2"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            logger.warning(
                "Password mismatch during registration from email %s",
                attrs.get("email", "-")
            )
            raise ValidationError({"password": _("Password don't match")})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user
    
class UserSerializer(ModelSerializer):
    """
    Serializer for User model
    """
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "avatar", "date_joined"]
        read_only_fields = fields


class LanguageUpdateSerializer(Serializer):
    """
    Serializer for Language update
    """
    language = ChoiceField(choices=["en", "ru", "kk"])

    def update(self, instance, validated_data):
        instance.language = validated_data["language"]
        instance.save(update_fields = ["language"])
        return instance
    

class TimezoneUpdateSerializer(Serializer):
    """
    Serializer for Timezone update
    """
    TIMEZONE_MAX_LENGHT = 50


    timezone = CharField(max_length=TIMEZONE_MAX_LENGHT)

    def validate_timezone(self, value):
        if value not in pytz.all_timezones:
            raise ValidationError(_("Invalid timezone"))
        return value
    
    def update(self, instance, validated_data):
        instance.timezone = validated_data["timezone"]
        instance.save(update_fields=["timezone"])
        return instance