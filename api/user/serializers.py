from logging import getLogger

import requests
import time
from django.conf import settings

from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile
from api.core.utils import cleansed_username

UserModel = get_user_model()
logger = getLogger(__name__)


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    username = serializers.SerializerMethodField()
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

    def get_username(self, obj):
        return cleansed_username(obj)

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
        if not settings.SSO_ENABLED:
            return None
        url = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INFO_URL"]
        token = self.context.get("token", None)
        auth_string = f"Bearer {token}"
        headers = {
            'Authorization': auth_string,
            'cache-control': "no-cache"
            }
        try:
            response = requests.request("GET", url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("permitted_applications", None)
            else:
                logger.warning("User info endpoint on SSO was not successful")
                return None
        except Exception as exc:
            logger.error(f"Error occurred while requesting user info from SSO, {exc}")
            raise
        
        return None
