from logging import getLogger

import requests
import time
from django.conf import settings
from django.core.cache import cache

from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile
from api.core.utils import cleansed_username

UserModel = get_user_model()
logger = getLogger(__name__)


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
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
        sso_data = cache.get_or_set("sso_data", self._sso_user_data(), 72000)
        if sso_data:
            email = sso_data.get("email")
        return email

    def get_username(self, obj):
        # username = cleansed_username(obj)
        sso_data = cache.get_or_set("sso_data", self._sso_user_data(), 72000)
        if sso_data:
            return f"{sso_data.get('first_name', '')} {sso_data.get('last_name', '')}"
        return None

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

    def _sso_user_data(self):
        if not settings.SSO_ENABLED:
            return None
        url = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INFO_URL"]
        token = self.context.get("token", None)
        if token is None:
            logger.warning("token is empty")
        auth_string = f"Bearer {token}"
        headers = {
            'Authorization': auth_string,
            'Cache-Control': "no-cache"
            }
        try:
            response = requests.request("GET", url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("User info endpoint on SSO was not successful")
                return None
        except Exception as exc:
            logger.error(f"Error occurred while requesting user info from SSO, {exc}")
            return None

    def get_permitted_applications(self, obj):
        print(self.context)
        sso_data = cache.get_or_set("sso_data", self._sso_user_data(), 72000)
        if sso_data:
            return sso_data.get("permitted_applications", None)
        return None
