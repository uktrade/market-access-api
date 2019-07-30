from django.contrib.auth import get_user_model

from rest_framework import serializers

from api.collaboration.models import TeamMember

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ['email', 'first_name', 'last_name']


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

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}
