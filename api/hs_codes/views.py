from rest_framework import generics

from api.metadata.models import HSCode
from .serializers import HSCodeSerializer


class HSCodeList(generics.ListAPIView):
    queryset = HSCode.objects.all()
    serializer_class = HSCodeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        codes = self.request.query_params.get("codes")
        if codes:
            queryset = queryset.filter(code__in=codes.split(","))

        return queryset


class HSCodeDetail(generics.RetrieveAPIView):
    serializer_class = HSCodeSerializer

    def get_object(self):
        try:
            return HSCode.objects.filter(code=self.kwargs.get("code")).latest("id")
        except HSCode.DoesNotExist:
            raise Http404("HS Code does not exist")
