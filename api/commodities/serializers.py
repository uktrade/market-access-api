from rest_framework import serializers

from .models import Commodity


class CommoditySerializer(serializers.ModelSerializer):

    class Meta:
        model = Commodity
        fields = (
            "id",
            "code",
            "suffix",
            "level",
            "description",
            "full_name",
        )
