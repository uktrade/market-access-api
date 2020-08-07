from rest_framework import serializers

from .models import WTOCommittee


class WTOCommitteeField(serializers.UUIDField):
    def to_representation(self, value):
        return {
            "id": value.id,
            "name": value.name,
        }

    def to_internal_value(self, data):
        if not data:
            return

        value = super().to_internal_value(data)
        try:
            return WTOCommittee.objects.get(pk=value)
        except WTOCommittee.DoesNotExist:
            raise serializers.ValidationError("WTO committee not found")
