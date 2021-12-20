from logging import getLogger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from rest_framework import serializers

from api.core.utils import cleansed_username
from api.user.helpers import get_username
from api.user.models import Profile, SavedSearch
from api.user.staff_sso import sso

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
    permissions = serializers.SerializerMethodField()
    has_approved_digital_trade_email = serializers.SerializerMethodField()

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
            "permitted_applications",
            "has_approved_digital_trade_email",
            "permissions",
            "is_active",
            "is_superuser",
        )

    def get_email(self, obj):
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get("email", None)
        return obj.email

    def get_first_name(self, obj):
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get("first_name", None)
        return obj.first_name

    def get_last_name(self, obj):
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get("last_name", None)
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
            return sso_me.get("permitted_applications", None)
        return None

    def get_has_approved_digital_trade_email(self, obj):
        email_domain = obj.email.split("@")[-1].lower()
        return email_domain in settings.APPROVED_DIGITAL_TRADE_EMAIL_DOMAINS

    def get_permissions(self, obj):
        return (
            Permission.objects.filter(Q(user=obj) | Q(group__user=obj))
            .distinct()
            .values_list("codename", flat=True)
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["sso_user_id"]


class NestedGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    groups = NestedGroupSerializer(many=True, required=False)

    class Meta:
        model = UserModel
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "profile",
            "permissions",
            "groups",
            "is_active",
            "is_superuser",
        )

    def get_full_name(self, obj):
        return cleansed_username(obj)

    def get_permissions(self, obj):
        return (
            Permission.objects.filter(Q(user=obj) | Q(group__user=obj))
            .distinct()
            .values_list("codename", flat=True)
        )

    def get_validated_group_ids(self):
        group_ids = []
        for group in self.initial_data.get("groups"):
            try:
                group_ids.append(int(group.get("id")))
            except ValueError:
                continue
        return Group.objects.filter(pk__in=group_ids).values_list("id", flat=True)

    def update(self, instance, validated_data):
        if validated_data.pop("groups") is not None:
            group_ids = self.get_validated_group_ids()
            instance.groups.set(group_ids)
        return super().update(instance, validated_data)


class UserMinimalDetailSerializer(UserDetailSerializer):
    class Meta:
        model = UserModel
        fields = (
            "email",
            "first_name",
            "last_name",
            "full_name",
        )


class UserListSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    full_name = serializers.SerializerMethodField()
    groups = NestedGroupSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = UserModel
        fields = [
            "id",
            "profile",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "groups",
        ]

    def get_full_name(self, obj):
        return cleansed_username(obj)


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = [
            "id",
            "name",
            "filters",
            "barrier_count",
            "new_barrier_ids",
            "new_count",
            "updated_barrier_ids",
            "updated_count",
            "notify_about_additions",
            "notify_about_updates",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class GroupSerializer(serializers.ModelSerializer):
    users = UserListSerializer(source="user_set", many=True, read_only=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "users",
        ]
