from rest_framework import serializers

from api.barriers.fields import StatusField


# TODO : standard list serialiser may suffice and the following not required base on final designs
class BarrierRelatedListSerializer(serializers.Serializer):
    summary = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    id = serializers.UUIDField(read_only=True)
    reported_on = serializers.DateTimeField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    status = StatusField(required=False)
    location = serializers.CharField(read_only=True)
    similarity = serializers.FloatField(read_only=True)


class SearchRequest(serializers.Serializer):
    search_term = serializers.CharField(required=True)
