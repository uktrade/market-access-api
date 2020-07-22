from rest_framework import serializers

from api.barriers.models import BarrierCommodity
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


class BarrierCommoditySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='commodity.id')
    description = serializers.ReadOnlyField(source='commodity.description')
    full_description = serializers.ReadOnlyField(source='commodity.full_description')

    class Meta:
        model = BarrierCommodity
        fields = (
            "id",
            "code",
            "description",
            "full_description",
        )
