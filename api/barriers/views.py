from rest_framework import generics

from api.core.auth import IsMAServer, IsMAUser
from api.barriers.models import BarrierInstance
from api.barriers.serializers import BarrierInstanceSerializer

PERMISSION_CLASSES = (IsMAServer, IsMAUser)

class BarrierList(generics.ListAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierInstanceSerializer


class BarrierDetail(generics.RetrieveAPIView):
    permission_classes = PERMISSION_CLASSES
    lookup_field = "pk"
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierInstanceSerializer
