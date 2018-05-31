from rest_framework import generics
from rest_framework.decorators import permission_classes

from api.core.auth import IsMAServer, IsMAUser
from api.barriers.models import Barrier
from api.barriers.serializers import BarrierListSerializer, BarrierDetailSerializer

PERMISSION_CLASSES = (IsMAServer, IsMAUser)


class BarrierList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = Barrier.objects.all()
    serializer_class = BarrierListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class BarrierDetail(generics.RetrieveUpdateAPIView):
    permission_classes = PERMISSION_CLASSES

    lookup_field = 'pk'
    queryset = Barrier.objects.all()
    serializer_class = BarrierDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
