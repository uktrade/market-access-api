from django.db.models import Max
from django.http import Http404
from rest_framework import generics

from .models import Commodity
from .serializers import CommoditySerializer


class CommodityList(generics.ListAPIView):
    queryset = Commodity.objects.all()
    serializer_class = CommoditySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        codes = self.request.query_params.get("codes")
        if codes:
            cleaned_codes = [code[:10].ljust(10, "0") for code in codes.split(",")]
            latest_version = Commodity.objects.aggregate(Max('version')).get("version__max")
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
