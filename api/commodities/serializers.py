import logging

from rest_framework import serializers

from api.barriers.models import BarrierCommodity
from api.metadata.fields import CountryField, TradingBlocField

from .models import Commodity

logger = logging.getLogger(__name__)


class CommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commodity
        fields = (
            "id",
            "code",
            "suffix",
            "level",
            "description",
            "full_description",
        )


class CommoditySearchListSerializer(serializers.Serializer):
    description = serializers.CharField()
    hs_code = serializers.CharField()
    similarity = serializers.FloatField()

    def get_similarity(self, obj):

        logger.critical("--------------------------------------")
        logger.critical("cleaning similarity")
        logger.critical("--------------------------------------")

        return obj.similarity


class BarrierCommoditySerializer(serializers.ModelSerializer):
    country = CountryField(allow_null=True)
    trading_bloc = TradingBlocField(allow_blank=True)
    commodity = CommoditySerializer()

    class Meta:
        model = BarrierCommodity
        fields = (
            "commodity",
            "code",
            "country",
            "trading_bloc",
        )
