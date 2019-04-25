from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile, WatchList
from api.core.utils import cleansed_username

UserModel = get_user_model()


class WatchListSerializer(serializers.ModelSerializer):
    """ Serialzer for User Watch List """

    created_by = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = WatchList
        fields = (
            "id",
            "name",
            "filter",
        )

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    username = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    internal = serializers.SerializerMethodField()
    watch_lists = serializers.SerializerMethodField()

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
            "watch_lists",
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

    def get_watch_lists(self, obj):
        return [
            {
                "id": obj.watch_list.id,
                "name": obj.watch_list.name,
                "filter": obj.watch_list.filter,
            }
            for watch_list in obj.watch_lists.all()
        ]
