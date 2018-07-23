from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.barriers.models import (
    BarrierContributor,
    BarrierInstance,
    BarrierInteraction
)
from api.barriers.serializers import (
    BarrierContributorSerializer,
    BarrierInstanceSerializer,
    BarrierInteractionSerializer,
    BarrierListSerializer,
    BarrierResolveSerializer,
)
from api.core.auth import IsMAServer, IsMAUser
from api.metadata.constants import BARRIER_INTERACTION_TYPE

PERMISSION_CLASSES = (IsMAServer, IsMAUser)


@api_view(["GET"])
def barrier_count(request):
    return Response({"count": BarrierInstance.objects.count()})


class BarrierList(generics.ListAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierListSerializer


class BarrierDetail(generics.RetrieveAPIView):
    permission_classes = PERMISSION_CLASSES
    lookup_field = "pk"
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierInstanceSerializer


class BarrierInstanceInteraction(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = BarrierInteraction.objects.all()
    serializer_class = BarrierInteractionSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("barrier_pk"))

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("barrier_pk"))
        kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
        if settings.DEBUG is False:
            serializer.save(
                barrier=barrier_obj, kind=kind, created_by=self.request.user
            )
        else:
            serializer.save(barrier=barrier_obj, kind=kind)


class BarrierInstanceContributor(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = BarrierContributor.objects.all()
    serializer_class = BarrierContributorSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("barrier_pk"))

    # def perform_create(self, serializer):
    #     barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("barrier_pk"))
    #     if settings.DEBUG is False:
    #         serializer.save(
    #             barrier=barrier_obj, created_by=self.request.user
    #         )
    #     else:
    #         serializer.save(barrier=barrier_obj)


class BarrierResolve(generics.UpdateAPIView):
    permission_classes = PERMISSION_CLASSES

    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierResolveSerializer

    # def get_queryset(self):
    #     return self.queryset.filter(id=self.kwargs.get('pk'))

    @transaction.atomic()
    def perform_update(self, serializer):
        barrier = self.get_object()
        barrier.resolve(self.request.user)


class BarrierHibernate(generics.UpdateAPIView):
    permission_classes = PERMISSION_CLASSES

    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierResolveSerializer

    # def get_queryset(self):
    #     return self.queryset.filter(id=self.kwargs.get('pk'))

    @transaction.atomic()
    def perform_update(self, serializer):
        barrier = self.get_object()
        barrier.hibernate(self.request.user)
