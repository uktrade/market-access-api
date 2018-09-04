from collections import defaultdict
from dateutil.parser import parse

from django.conf import settings
from django.db import transaction
from django.db.models import Q
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
    BarrierReportStage,
)
from api.barriers.serializers import (
    BarrierContributorSerializer,
    BarrierStaticStatusSerializer,
    BarrierInstanceSerializer,
    BarrierInteractionSerializer,
    BarrierListSerializer,
    BarrierResolveSerializer,
    BarrierReportSerializer,
)
from api.metadata.constants import (
    BARRIER_INTERACTION_TYPE,
    CONTRIBUTOR_TYPE
)
from api.metadata.models import BarrierType


@api_view(["GET"])
def barrier_count(request):
    return Response({"count": BarrierInstance.objects.count()})


class BarrierReportBase(object):
    def _update_stages(self, serializer, user):
        report_id = serializer.data.get("id")
        report = BarrierInstance.objects.get(id=report_id)
        progress = report.current_progress()
        for new_stage, new_status in progress:
            try:
                report_stage = BarrierReportStage.objects.get(barrier=report, stage=new_stage)
                report_stage.status = new_status
                report_stage.save()
            except BarrierReportStage.DoesNotExist:
                BarrierReportStage(
                    barrier=report, stage=new_stage, status=new_status
                ).save()
            if settings.DEBUG is False:
                report_stage = BarrierReportStage.objects.get(barrier=report, stage=new_stage)
                report_stage.user = user
                report_stage.save()
    
    class Meta:
        abstract = True


class BarrierReportList(BarrierReportBase, generics.ListCreateAPIView):
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierReportSerializer

    def get_queryset(self):
        return self.queryset.filter(status=0)

    @transaction.atomic()
    def perform_create(self, serializer):
        if settings.DEBUG is False:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
        self._update_stages(serializer, self.request.user)


class BarrierReportDetail(BarrierReportBase, generics.RetrieveUpdateAPIView):

    lookup_field = "pk"
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierReportSerializer

    @transaction.atomic()
    def perform_update(self, serializer):
        if self.request.data.get("barrier_type", None) is not None:
            barrier_type = get_object_or_404(BarrierType, pk=self.request.data.get("barrier_type"))
            serializer.save(barrier_type=barrier_type)
        else:
            serializer.save()
        self._update_stages(serializer, self.request.user)


class BarrierReportSubmit(generics.UpdateAPIView):

    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierReportSerializer

    @transaction.atomic()
    def perform_update(self, serializer):
        """
        Validates report for mandatory fields
        Changes status of the report
        Creates a Barrier Instance out of the report
        Sets up default status
        Sets up contributor where appropriate
        """
        # validate and complete a report
        report = self.get_object()
        report.submit_report()

        # sort out contributors
        if settings.DEBUG is False:
            if report.support_type == 2:
                try:
                    BarrierContributor.objects.get(
                        barrier=report, 
                        contributor=report.created_by,
                        kind=CONTRIBUTOR_TYPE['LEAD'],
                        is_active=True
                    )
                except BarrierContributor.DoesNotExist:
                    BarrierContributor(
                        barrier=report,
                        contributor=report.created_by,
                        kind=CONTRIBUTOR_TYPE['LEAD'],
                        created_by=self.request.user
                    ).save()


class BarrierList(generics.ListCreateAPIView):
    queryset = BarrierInstance.objects.all()
    serializer_class = BarrierListSerializer

    def get_queryset(self):
        return self.queryset.filter(~Q(status=0))


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
    def _create(self, serializer, barrier_id, barrier_status, barrier_summary, status_date=None):
        barrier_obj = get_object_or_404(BarrierInstance, pk=barrier_id)
        if status_date is None:
            status_date = timezone.now()
        if settings.DEBUG is False:
            serializer.save(
                barrier=barrier_obj,
                status=barrier_status,
                summary=barrier_summary,
                status_date=status_date,
                created_by=self.request.user
            )
        else:
            serializer.save(
                barrier=barrier_obj,
                status=barrier_status,
                summary=barrier_summary,
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
        if errors:
            message = {
                "fields": errors
            }
            raise serializers.ValidationError(message)
        self._create(
            serializer,
            self.kwargs.get("pk"),
            4,
            self.request.data.get("summary"),
            self.request.data.get("status_date")
        )


class BarrierHibernate(generics.CreateAPIView, BarrierStatusBase):

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        self._create(serializer, self.kwargs.get("pk"), 5, self.request.data.get("summary"))


class BarrierOpen(generics.CreateAPIView, BarrierStatusBase):

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        self._create(serializer, self.kwargs.get("pk"), 2, self.request.data.get("summary"))


class BarrierStatusList(generics.ListCreateAPIView, BarrierStatusBase):

    queryset = BarrierStatus.objects.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("barrier_pk"))

    def perform_create(self, serializer):
        self._create(
            serializer,
            self.request,
            self.kwargs.get("pk"),
            self.request.data.get("status")
        )
