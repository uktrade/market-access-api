from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile, Watchlist
from api.core.utils import cleansed_username

UserModel = get_user_model()


class WatchlistSerializer(serializers.ModelSerializer):
    """ Serialzer for User Watchlist """

    class Meta:
        model = Watchlist
        fields = (
            "id",
            "name",
            "filter",
        )


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
                "id": watch_list.id,
                "name": watch_list.name,
                "filter": watch_list.filter,
            }
            for watch_list in obj.profile.watch_lists.all()
        ]
