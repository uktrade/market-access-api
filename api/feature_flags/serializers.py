from rest_framework import serializers


class FlagSerializer(serializers.Serializer):
    name = serializers.CharField()
