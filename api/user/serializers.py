from rest_framework import serializers

from django.contrib.auth import get_user_model

from api.user.models import Profile

UserModel = get_user_model()


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    location = serializers.SerializerMethodField()

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
        )

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