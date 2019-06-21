from logging import getLogger

import time
from django.conf import settings
from django.core.cache import cache

from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile
from api.core.utils import cleansed_username
from api.user.utils import get_sso_user_data

UserModel = get_user_model()
logger = getLogger(__name__)


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    internal = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()
    permitted_applications = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = (
            "id",
            "username",
            "last_login",
            "first_name",
            "last_name",
            "email",
            "location",
            "internal",
            "user_profile",
            "permitted_applications"
        )

    def get_email(self, obj):
        email = obj.username
        sso_data = cache.get_or_set("sso_data", get_sso_user_data(), 72000)
        if sso_data:
            return sso_data.get("email")
        return email

    def get_first_name(self, obj):
        first_name = obj.username
        sso_data = cache.get_or_set("sso_data", get_sso_user_data(), 72000)
        if sso_data:
            return sso_data.get("first_name")
        return first_name

    def get_last_name(self, obj):
        last_name = obj.username
        sso_data = cache.get_or_set("sso_data", get_sso_user_data(), 72000)
        if sso_data:
            return sso_data.get("last_name")
        return last_name

    def get_username(self, obj):
        username = cleansed_username(obj)
        sso_data = cache.get_or_set("sso_data", get_sso_user_data(), 72000)
        if sso_data:
            return f"{sso_data.get('first_name', '')} {sso_data.get('last_name', '')}"
        return username

    def get_location(self, obj):
        try:
            if obj.profile is not None and obj.profile.location is not None:
                return obj.profile.location
            else:
                return None
        except Profile.DoesNotExist:
            return None
        except AttributeError:
            return None

    def get_internal(self, obj):
        try:
            if obj.profile is not None and obj.profile.internal is not None:
                return obj.profile.internal
            else:
                return False
        except Profile.DoesNotExist:
            return False
        except AttributeError:
            return False

    def get_user_profile(self, obj):
        try:
            if obj.profile is not None and obj.profile.user_profile is not None:
                return obj.profile.user_profile
            else:
                return None
        except Profile.DoesNotExist:
            return None
        except AttributeError:
            return None

    def get_permitted_applications(self, obj):
        sso_data = cache.get_or_set("sso_data", get_sso_user_data(), 72000)
        if sso_data:
            return sso_data.get("permitted_applications", None)
        return None
