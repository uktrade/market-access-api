import datetime

from rest_framework import serializers

from api.barriers.models import EstimatedResolutionDateRequest


class ERDRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimatedResolutionDateRequest
        fields = "__all__"


class ERDResponseSerializer(ERDRequestSerializer):
    class Meta:
        model = EstimatedResolutionDateRequest
        fields = ('barrier', 'reason', 'estimated_resolution_date', 'created_by', 'status', 'created_on')


class CreateERDRequestSerializer(ERDRequestSerializer):
    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        erd = data.get('estimated_resolution_date')
        if erd and erd < datetime.date.today().replace(day=1):
            raise serializers.ValidationError({"estimated_resolution_date": "Must be in future"})
        return data


class PatchERDRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=EstimatedResolutionDateRequest.STATUSES, required=True)
