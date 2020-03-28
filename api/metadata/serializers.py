from rest_framework import serializers

from api.metadata.models import BarrierTag


class BarrierTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierTag
        fields = (
            "id",
            "title",
            "show_at_reporting",
        )
