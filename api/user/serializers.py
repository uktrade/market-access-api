from logging import getLogger

import time
from django.conf import settings
from django.core.cache import cache

from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile, SavedSearch
from api.core.utils import cleansed_username
from api.user.utils import get_username
from api.user.staff_sso import StaffSSO

UserModel = get_user_model()
logger = getLogger(__name__)
sso = StaffSSO()


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
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get('email', None)
        return obj.email

    def get_first_name(self, obj):
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get('first_name', None)
        return obj.first_name

    def get_last_name(self, obj):
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get('last_name', None)
        return obj.last_name

    def get_username(self, obj):
        return get_username(obj, self.context)

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
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get('permitted_applications', None)
        return None


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ["sso_user_id"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            'profile',
            'email',
            'first_name',
            'last_name',
            'full_name',
        ]

    def get_email(self, obj):
        return obj.email

    def get_full_name(self, obj):
        return cleansed_username(obj)


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = [
            'id',
            'name',
            'filters',
            'barrier_count',
            'new_count',
            'updated_count',
        ]
