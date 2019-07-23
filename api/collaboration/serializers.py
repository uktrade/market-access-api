from rest_framework import serializers

from api.collaboration.models import TeamMember

class BarrierTeamSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers team members """

    created_by = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = (
            "id",
            "user",
            "role",
            "is_active",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
        )
        read_only_fields = (
            "id",
            "name",
            "email",
            "modified_on",
            "modified_by",
            "created_on",
            "created_by"
        )

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}

    def get_user(self, obj):
        if obj.user is None:
            return None

        name = f"{obj.user.first_name} {obj.user.lastname}"
        return {"name": name, "email": obj.user.email}
