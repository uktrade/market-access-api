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
            queryset = queryset.filter(code__in=codes.split(","))

        return queryset


class CommodityDetail(generics.RetrieveAPIView):
    serializer_class = CommoditySerializer

    def get_object(self):
        try:
            return Commodity.objects.filter(code=self.kwargs.get("code")).latest("id")
        except Commodity.DoesNotExist:
            raise Http404("Commodity does not exist")
