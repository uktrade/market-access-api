from rest_framework import serializers

from api.barriers.fields import BarrierPriorityField, StatusField


class BarrierRelatedListSerializer(serializers.Serializer):
    summary = serializers.CharField()
    title = serializers.CharField()
    id = serializers.CharField()
    reported_on = serializers.DateTimeField()
    modified_on = serializers.DateTimeField()
    status = StatusField()
    location = serializers.SerializerMethodField()
    similarity = serializers.FloatField()
    priority = BarrierPriorityField(required=False)
    top_priority_status = serializers.CharField()

    def get_location(self, obj):
        try:
            return obj.location or ""
        except Exception:
            return ""


class SearchRequest(serializers.Serializer):
    search_term = serializers.CharField(required=True)
