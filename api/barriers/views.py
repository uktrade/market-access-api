import json
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import permission_classes

from api.core.auth import IsMAServer, IsMAUser
from api.barriers.models import Barrier, BarrierReportStage, ReportStage
from api.metadata.constants import REPORT_STATUS
from api.barriers.serializers import (
    BarrierListSerializer,
    BarrierDetailSerializer,
    BarrierReportStageListSerializer
)

PERMISSION_CLASSES = (IsMAServer, IsMAUser)


class BarrierList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = Barrier.objects.all()
    serializer_class = BarrierListSerializer

    def list(self, request, *args, **kwargs):
        if self.kwargs['status']:
            self.queryset = self.filter_queryset(self.get_queryset().filter(
                status=self.kwargs['status'])
            )

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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


class BarrierReportStagesList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES

    # lookup_field = 'pk'
    queryset = BarrierReportStage.objects.all()
    serializer_class = BarrierReportStageListSerializer

    # def list(self, request, *args, **kwargs):
    #     # queryset = self.filter_queryset(self.get_queryset().filter(
    #     #     barrier_id=self.kwargs['pk'])
    #     # )
    #     serializer = self.get_serializer(self.get_queryset(), many=True)
    #     return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create and one-time upload URL generation."""
        barrier_id = self.kwargs['pk']
        barrier = Barrier.objects.get(id=barrier_id)
        stage_data = json.loads(request.body)
        stage = ReportStage.objects.get(code=stage_data['stage'])
        barrier_stage = BarrierReportStage(
            stage=stage, barrier=barrier, status=stage_data['status']).save()
        # serializer = BarrierDetailSerializer(data=request.data)
        # if serializer.is_valid():
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # response = super().create(request, *args, **kwargs)

        # return response
        return Response(status=status.HTTP_201_CREATED)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
