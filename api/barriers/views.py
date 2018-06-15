import json
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
            # self.queryset = self.filter_queryset(self.get_queryset().filter(
            #     status=self.kwargs['status'])
            # )
        return self.queryset

    # def list(self, request, *args, **kwargs):
    #     if self.kwargs['status']:
    #         self.queryset = self.filter_queryset(self.get_queryset().filter(
    #             status=self.kwargs['status'])
    #         )

    #     queryset = self.filter_queryset(self.get_queryset())
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

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

    lookup_field = 'pk'
    queryset = BarrierReportStage.objects.all()
    serializer_class = BarrierReportStageSerializer

    # def get_queryset(self):

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get('barrier_pk'))

    # def list(self, request, *args, **kwargs):
    #     self.queryset = self.filter_queryset(self.get_queryset().filter(
    #         barrier_id=self.kwargs['pk'])
    #     )
    #     serializer = self.get_serializer(self.get_queryset(), many=True)
    #     return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = {
            'barrier': self.kwargs['pk'],
            'stage': request.data['stage'],
            'status': request.data['status']
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
