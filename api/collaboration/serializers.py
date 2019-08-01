from django.contrib.auth import get_user_model

from rest_framework import serializers

from api.collaboration.models import TeamMember
from api.user.models import Profile

UserModel = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ["sso_user_id"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = UserModel
        fields = ['profile', 'email', 'first_name', 'last_name']


class BarrierTeamSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers team members """

    created_by = serializers.SerializerMethodField()
    user = UserSerializer()

    class Meta:
        model = TeamMember
        fields = (
            "id",
            "user",
            "role",
            "is_active",
            "created_on",
            "created_by",
        )
        read_only_fields = (
            "id",
            "user",
            "created_by",
            "created_on"
        )

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}
