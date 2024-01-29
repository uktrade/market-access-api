from rest_framework import serializers


class BarrierReportSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    user = serializers.CharField()
    created_on = serializers.DateTimeField()
    modified_on = serializers.DateTimeField()
