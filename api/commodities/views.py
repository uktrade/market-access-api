import logging

from django.db.models import Max
from django.http import Http404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.related_barriers.tariff_search import TariffSearchManager

from .models import Commodity
from .serializers import CommoditySearchListSerializer, CommoditySerializer

logger = logging.getLogger(__name__)


class CommodityList(generics.ListAPIView):
    queryset = Commodity.objects.all()
    serializer_class = CommoditySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        codes = self.request.query_params.get("codes")
        if codes:
            cleaned_codes = [code[:10].ljust(10, "0") for code in codes.split(",")]
            latest_version = Commodity.objects.aggregate(Max("version")).get(
                "version__max"
            )
            queryset = queryset.filter(
                code__in=cleaned_codes,
                is_leaf=True,
                version=latest_version,
            ).order_by("code")
        return queryset


class CommodityDetail(generics.RetrieveAPIView):
    serializer_class = CommoditySerializer

    def get_object(self):
        cleaned_code = self.kwargs.get("code")[:10].ljust(10, "0")

        try:
            return Commodity.objects.filter(
                code=cleaned_code,
                is_leaf=True,
            ).latest("version")
        except Commodity.DoesNotExist:
            raise Http404("Commodity does not exist")


@api_view(["GET"])
def related_barriers_view(request) -> Response:
    query = request.GET.get("query")

    tariff_search_manager = TariffSearchManager()
    result = tariff_search_manager.get_similarities(query)
    serializer = CommoditySearchListSerializer(result, many=True)

    return Response(status=status.HTTP_200_OK, data=serializer.data)
