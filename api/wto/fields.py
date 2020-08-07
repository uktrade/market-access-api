from rest_framework import serializers

from .models import WTOCommittee


class WTOCommitteeField(serializers.Field):
    def to_representation(self, value):
        return {
            "id": value.id,
            "name": value.name,
        }

    def to_internal_value(self, data):
        try:
            return WTOCommittee.objects.get(pk=data)
        except WTOCommittee.DoesNotExist:
            raise serializers.ValidationError("Priority not found")
