import json
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import permission_classes

from api.core.auth import IsMAServer, IsMAUser
from api.barriers.models import Barrier, BarrierReportStage, ReportStage
from api.metadata.constants import REPORT_STATUS
from api.barriers.serializers import (
    BarrierListSerializer,
    BarrierDetailSerializer,
    BarrierReportStageSerializer
)

PERMISSION_CLASSES = (IsMAServer, IsMAUser)


class BarrierList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = Barrier.objects.all()
    serializer_class = BarrierListSerializer

    def get_queryset(self):
        if self.kwargs['status']:
            return self.queryset.filter(status=self.kwargs['status'])
        return self.queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if settings.DEBUG is False:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()


class BarrierDetail(generics.RetrieveUpdateAPIView):
    permission_classes = PERMISSION_CLASSES

    lookup_field = 'pk'
    queryset = Barrier.objects.all()
    serializer_class = BarrierDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class BarrierReportStagesList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES

    queryset = BarrierReportStage.objects.all()
    serializer_class = BarrierReportStageSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get('barrier_pk'))

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(Barrier, pk=self.kwargs.get('barrier_pk'))
        stage_obj = get_object_or_404(ReportStage, pk=self.request.data.get('stage'))
        if settings.DEBUG is False:
            serializer.save(barrier=barrier_obj, stage=stage_obj, created_by=self.request.user)
        else:
            serializer.save(barrier=barrier_obj, stage=stage_obj)
