import datetime

from rest_framework import serializers

from api.barriers.models import EstimatedResolutionDateRequest
from api.core.utils import cleansed_username


class ERDResponseSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = EstimatedResolutionDateRequest
        fields = (
            "barrier",
            "reason",
            "estimated_resolution_date",
            "created_by",
            "status",
            "created_on",
        )

    def get_created_by(self, obj):
        if not obj.created_by:
            return ""

        return cleansed_username(obj.created_by)


class CreateERDRequestSerializer(serializers.Serializer):
    reason = serializers.CharField()
    estimated_resolution_date = serializers.DateField(allow_null=True)

    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        erd = data.get("estimated_resolution_date")
        if erd and erd < datetime.date.today().replace(day=1):
            raise serializers.ValidationError(
                {"estimated_resolution_date": "Must be in future"}
            )
        return data


class RejectERDRequestSerializer(serializers.Serializer):
    reason = serializers.CharField()
