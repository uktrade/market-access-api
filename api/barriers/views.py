from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.core.auth import IsMAServer, IsMAUser
from api.barriers.models import BarrierInstance
from api.barriers.serializers import BarrierInstanceSerializer, BarrierListSerializer

PERMISSION_CLASSES = (IsMAServer, IsMAUser)

class BarrierList(generics.ListAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierListSerializer


class BarrierDetail(generics.RetrieveAPIView):
    permission_classes = PERMISSION_CLASSES
    lookup_field = "pk"
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierInstanceSerializer


@api_view(["GET"])
def barrier_count(request):
    return Response({"count": BarrierInstance.objects.count()})