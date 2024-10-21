from logging import getLogger

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from rest_framework import serializers
from sentry_sdk import push_scope

from api.core.utils import cleansed_username
from api.user.helpers import get_username
from api.user.models import Profile, SavedSearch, UserActvitiyLog
from api.user.staff_sso import sso

UserModel = get_user_model()
logger = getLogger(__name__)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


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
    groups = GroupSerializer(many=True, required=False, read_only=True)
    sso_user_id = serializers.CharField(source="profile.sso_user_id", allow_null=True)

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
            "permissions",
            "is_active",
            "is_superuser",
            "groups",
            "sso_user_id",
        )

    def get_email(self, obj):
        sso_me = sso.get_logged_in_user_details(self.context)
        if sso_me is not None:
            return sso_me.get("email")
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

    def get_permissions(self, obj):
        return (
            Permission.objects.filter(Q(user=obj) | Q(group__user=obj))
            .distinct()
            .values_list("codename", flat=True)
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "sso_user_id",
            "sectors",
            "policy_teams",
            "organisations",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, required=False)

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

    def update_profile(self, instance, validated_data):
        # Update the users profile
        profile_update = validated_data.pop("profile", None)

        if profile_update is not None:
            # update the related profile
            sectors = profile_update.pop("sectors", None)
            policy_teams = profile_update.pop("policy_teams", None)
            organisations = profile_update.pop("organisations", None)
            # get current profile
            profile = instance.profile
            if sectors:
                profile.sectors = sectors
            if policy_teams:
                profile.policy_teams.clear()
                for team in policy_teams:
                    profile.policy_teams.add(team)
            if organisations:
                profile.organisations.clear()
                for organisation in organisations:
                    profile.organisations.add(organisation)

    def update(self, instance, validated_data):

        if validated_data.pop("groups", None) is not None:
            group_ids = [
                int(each.get("id"))
                for each in self.initial_data.get("groups")
                if "id" in each
            ]
            group_queryset = Group.objects.filter(pk__in=group_ids)

            current_groups = set([group.name for group in instance.groups.all()])
            new_groups = set([group.name for group in group_queryset])

            # figuring out the delta
            groups_added = new_groups - current_groups
            groups_removed = current_groups - new_groups

            if groups_added:
                logger.info(
                    f"User {instance.id} has been added to the following groups: {groups_added}"
                )
                if "Administrator" in groups_added:
                    # the user has been granted administrator access
                    with push_scope() as scope:
                        scope.set_tag("always_alert", "true")
                        logger.critical(
                            f"User {instance.id} has been granted Administrator access"
                        )

            if groups_removed:
                logger.info(
                    f"User {instance.id} has been removed from the following groups: {groups_removed}"
                )
                if "Administrator" in groups_removed:
                    # the user has been removed from the administrator group
                    with push_scope() as scope:
                        scope.set_tag("always_alert", "true")
                        logger.critical(
                            f"User {instance.id} has been removed from the Administrator group"
                        )

            instance.groups.set(group_ids)
        if validated_data.pop("is_active", None) is not None:
            instance.is_active = False

        self.update_profile(instance, validated_data)

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
    groups = GroupSerializer(many=True, required=False, read_only=True)

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
            "is_active",
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


class UserActvitiyLogSerializer(serializers.ModelSerializer):

    user_id = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return obj.user.id

    def get_user_email(self, obj):
        return obj.user.email

    class Meta:
        model = UserActvitiyLog
        fields = [
            "id",
            "user_id",
            "user_email",
            "event_type",
            "event_description",
        ]
