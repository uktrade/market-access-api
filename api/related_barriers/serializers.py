from rest_framework import serializers

from api.barriers.fields import StatusField


class BarrierRelatedListSerializer(serializers.Serializer):
    summary = serializers.CharField()
    title = serializers.CharField()
    barrier_id = serializers.CharField()
    reported_on = serializers.DateTimeField()
    modified_on = serializers.DateTimeField()
    status = StatusField()
    location = serializers.SerializerMethodField()
    similarity = serializers.FloatField()

    def get_location(self, obj):
        try:
            return obj.location or ""
        except Exception:
            return ""


class SearchRequest(serializers.Serializer):
    search_term = serializers.CharField(required=True)
