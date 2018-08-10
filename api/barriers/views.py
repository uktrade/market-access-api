from collections import defaultdict
from dateutil.parser import parse

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.barriers.models import (
    BarrierContributor,
    BarrierInstance,
    BarrierInteraction,
    BarrierStatus,
)
from api.barriers.serializers import (
    BarrierContributorSerializer,
    BarrierStaticStatusSerializer,
    BarrierInstanceSerializer,
    BarrierInteractionSerializer,
    BarrierListSerializer,
    BarrierResolveSerializer,
    BarrierStatusSerializer,
)
from api.metadata.constants import BARRIER_INTERACTION_TYPE


@api_view(["GET"])
def barrier_count(request):
    return Response({"count": BarrierInstance.objects.count()})


class BarrierList(generics.ListAPIView):
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierListSerializer


class BarrierDetail(generics.RetrieveAPIView):
    lookup_field = "pk"
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierInstanceSerializer


class BarrierInstanceInteraction(generics.ListCreateAPIView):
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


class BarrierStatusBase(generics.GenericAPIView):
    def _create(self, serializer, barrier_id, status, summary, status_date=None):
        barrier_obj = get_object_or_404(BarrierInstance, pk=barrier_id)
        if status_date is None:
            status_date = timezone.now()
        if settings.DEBUG is False:
            serializer.save(
                barrier=barrier_obj,
                status=status,
                summary=summary,
                status_date=status_date,
                created_by=self.request.user
            )
        else:
            serializer.save(
                barrier=barrier_obj,
                status=status,
                summary=summary,
                status_date=status_date
            )


class BarrierResolve(generics.CreateAPIView, BarrierStatusBase):

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierResolveSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        errors = defaultdict(list)
        if self.request.data.get("summary", None) is None:
            errors["summary"] = "This field is required"
        if self.request.data.get("status_date", None) is None:
            errors["status_date"] = "This field is required"
        else:
            try:
                parse(self.request.data.get("status_date"))
            except ValueError:
                errors["status_date"] = "enter a valid date"
        if len(errors) > 0:
            message = {
                "fields": errors
            }
            raise serializers.ValidationError(message)
        self._create(serializer, self.kwargs.get("pk"), 4, self.request.data.get("summary"), self.request.data.get("status_date"))


class BarrierHibernate(generics.CreateAPIView, BarrierStatusBase):

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        self._create(serializer, self.kwargs.get("pk"), 5, self.request.data.get("summary"))


class BarrierOpen(generics.CreateAPIView, BarrierStatusBase):
    permission_classes = PERMISSION_CLASSES

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        self._create(serializer, self.kwargs.get("pk"), 2, self.request.data.get("summary"))


class BarrierStatusList(generics.ListCreateAPIView, BarrierStatusBase):

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("barrier_pk"))

    def perform_create(self, serializer):
        self._create(
            serializer,
            self.request,
            self.kwargs.get("pk"),
            self.request.data.get("status")
        )
