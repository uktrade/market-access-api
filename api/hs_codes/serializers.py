from rest_framework import serializers

from api.metadata.models import HSCode


class HSCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = HSCode
        fields = (
            "id",
            "code",
            "suffix",
            "level",
            "name",
            "full_name",
        )
