from rest_framework import serializers

from api.collaboration.models import TeamMember
from api.user.serializers import UserSerializer


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
            "default",
            "created_on",
            "created_by",
        )
        read_only_fields = (
            "id",
            "user",
            "default",
            "created_by",
            "created_on"
        )

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}
