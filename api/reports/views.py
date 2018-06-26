import json
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import permission_classes

from api.core.auth import IsMAServer, IsMAUser
from api.reports.models import Report, ReportStage, Stage
from api.metadata.constants import REPORT_STATUS
from api.reports.serializers import (
    ReportSerializer,
    ReportStageSerializer
)

PERMISSION_CLASSES = (IsMAServer, IsMAUser)


class ReportList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def get_queryset(self):
        if self.kwargs['status']:
            return self.queryset.filter(status=self.kwargs['status'])
        return self.queryset

    @transaction.atomic()
    def perform_create(self, serializer):
        if settings.DEBUG is False:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
        # Create first stage
        report_id = serializer.data.get('id')
        report = Report.objects.get(id=report_id)
        progress = report.current_stage()
        for new_stage, new_status in progress:
            try:
                report_stage = ReportStage.objects.get(report=report, stage=new_stage)
                report_stage.status = new_status
                report_stage.save()
            except ReportStage.DoesNotExist:
                report_stage = ReportStage(
                    report=report,
                    stage=new_stage,
                    status=new_status
                ).save()
            if settings.DEBUG is False:
                report_stage.user = self.request.user
                report_stage.save()


class ReportDetail(generics.RetrieveUpdateAPIView):
    permission_classes = PERMISSION_CLASSES

    lookup_field = 'pk'
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    @transaction.atomic()
    def perform_update(self, serializer):
        serializer.save()
        report_id = serializer.data.get('id')
        report = Report.objects.get(id=report_id)
        progress = report.current_stage()
        for new_stage, new_status in progress:
            try:
                report_stage = ReportStage.objects.get(report=report, stage=new_stage)
                report_stage.status = new_status
                report_stage.save()
            except ReportStage.DoesNotExist:
                report_stage = ReportStage(
                    report=report,
                    stage=new_stage,
                    status=new_status
                ).save()
            if settings.DEBUG is False:
                report_stage.user = self.request.user
                report_stage.save()


class ReportStagesList(generics.ListCreateAPIView):
    permission_classes = PERMISSION_CLASSES

    queryset = ReportStage.objects.all()
    serializer_class = ReportStageSerializer

    def get_queryset(self):
        return self.queryset.filter(report_id=self.kwargs.get('report_pk'))

    def perform_create(self, serializer):
        report_obj = get_object_or_404(Report, pk=self.kwargs.get('report_pk'))
        stage_obj = get_object_or_404(ReportStage, pk=self.request.data.get('stage'))
        if settings.DEBUG is False:
            serializer.save(report=report_obj, stage=stage_obj, created_by=self.request.user)
        else:
            serializer.save(report=report_obj, stage=stage_obj)


class ReportStageUpdate(generics.RetrieveUpdateAPIView):
    queryset = ReportStage.objects.all()
    serializer_class = ReportStageSerializer

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            report_id=self.kwargs.get('report_pk'),
            pk=self.kwargs.get('pk')
        )
