import logging
# DRF modules
from rest_framework.serializers import ModelSerializer, CharField, ValidationError
# Django modules
from django.contrib.auth import get_user_model


User = get_user_model()
logger = logging.getLogger(__name__)


PASSWORD_MIN_LENGTH = 8

class RegisterSerializer(ModelSerializer):
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
            raise ValidationError({"password": "Password don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user
    
class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "avatar", "date_joined"]
        read_only_fields = fields
