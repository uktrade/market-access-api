from collections import defaultdict
from dateutil.parser import parse

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.barriers.models import (
    BarrierContributor,
    BarrierInstance,
    BarrierInteraction,
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
from api.metadata.constants import BARRIER_INTERACTION_TYPE

from api.metadata.models import BarrierType


@api_view(["GET"])
def barrier_count(request):
    """ view to return number of barriers in the system """
    return Response({"count": BarrierInstance.barriers.count()})


class BarrierReportBase(object):
    def _update_stages(self, serializer, user):
        report_id = serializer.data.get("id")
        report = BarrierInstance.reports.get(id=report_id)
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
    queryset = BarrierInstance.reports.all()
    serializer_class = BarrierReportSerializer

    @transaction.atomic()
    def perform_create(self, serializer):
        if settings.DEBUG is False:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
        self._update_stages(serializer, self.request.user)


class BarrierReportDetail(BarrierReportBase, generics.RetrieveUpdateAPIView):

    lookup_field = "pk"
    queryset = BarrierInstance.reports.all()
    serializer_class = BarrierReportSerializer

    @transaction.atomic()
    def perform_update(self, serializer):
        serializer.save()
        self._update_stages(serializer, self.request.user)


class BarrierReportSubmit(generics.UpdateAPIView):

    queryset = BarrierInstance.reports.all()
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
        # validate and submit a report
        report = self.get_object()
        report.submit_report()

        # sort out contributors
        # if settings.DEBUG is False:
        #         try:
        #             BarrierContributor.objects.get(
        #                 barrier=report,
        #                 contributor=report.created_by,
        #                 kind=CONTRIBUTOR_TYPE['LEAD'],
        #                 is_active=True
        #             )
        #         except BarrierContributor.DoesNotExist:
        #             BarrierContributor(
        #                 barrier=report,
        #                 contributor=report.created_by,
        #                 kind=CONTRIBUTOR_TYPE['LEAD'],
        #                 created_by=self.request.user
        #             ).save()


class BarrierList(generics.ListAPIView):
    """
    Return a list of all the BarrierInstances with optional filtering.
    """
    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierListSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned barriers to a given export_country,
        by filtering against a `country` query parameter in the URL.
        """
        queryset = BarrierInstance.barriers.all()
        country = self.request.query_params.get("country", None)
        if country is not None:
            queryset = queryset.filter(export_country=country)
        return queryset


class BarrierDetail(generics.RetrieveUpdateAPIView):
    """
    Return details of a BarrierInstance
    Allows the barrier to be updated as well
    """
    lookup_field = "pk"
    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierInstanceSerializer

    @transaction.atomic()
    def perform_update(self, serializer):
        if self.request.data.get("barrier_type", None) is not None:
            barrier_type = get_object_or_404(BarrierType, pk=self.request.data.get("barrier_type"))
            serializer.save(barrier_type=barrier_type)
        else:
            serializer.save()


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

class BarrierInstanceHistory(GenericAPIView):
    def _get_barrier(self, barrier_id):
        """ Get BarrierInstance object or False if invalid ID """
        try:
            return BarrierInstance.barriers.get(id=barrier_id)
        except BarrierInstance.DoesNotExist:
            return False

    def get(self, request, barrier_pk):
        ignore_fields = ["modified_on"]
        barrier = BarrierInstance.barriers.get(id=barrier_pk)
        history = barrier.history.all().order_by("history_date")
        results = []
        for new_record in history:
            if new_record.history_type == "+":
                results.append({
                    "date": new_record.history_date,
                    "operation": "Add",
                    "event": "Report created",
                    "field": None,
                    "old_value": None,
                    "new_value": None,
                    "user": new_record.history_user.email if new_record.history_user else ""
                })
            else:
                delta = new_record.diff_against(old_record)
                for change in delta.changes:
                    if change.field not in ignore_fields:
                        if change.old is None:
                            operation = "Add"
                            event = "{} added to {}".format(change.new, change.field)
                            field = change.field
                            old_value = None
                            new_value = change.new
                        elif change.old is not None and change.new is not None:
                            operation = "Update"
                            event = "{} changed from {} to {}".format(change.field, change.old, change.new)
                            field = change.field
                            old_value = change.old
                            new_value = change.new
                        else:
                            operation = "Delete"
                            event = "{} deleted".format(change.field)
                            field = change.field
                            old_value = change.old
                            new_value = None
                        results.append(
                            {
                                "date": new_record.history_date,
                                "operation": operation,
                                "field": field,
                                "old_value": old_value,
                                "new_value": new_value,
                                "event": event,
                                "user": new_record.history_user.email if new_record.history_user else ""
                            }
                        )
            old_record = new_record
            response = {
                "barrier_id": barrier_pk,
                "history": results
            }
        return Response(response, status=status.HTTP_200_OK)


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


class BarrierStatusBase(generics.UpdateAPIView):
    def _create(self, serializer, barrier_id, barrier_status, barrier_summary, status_date=None):
        barrier_obj = get_object_or_404(BarrierInstance, pk=barrier_id)

        if status_date is None:
            status_date = timezone.now()

        serializer.save(
            status=barrier_status,
            summary=barrier_summary,
            status_date=status_date
        )
        # if settings.DEBUG is False:
        #     serializer.save(
        #         barrier=barrier_obj,
        #         status=barrier_status,
        #         summary=barrier_summary,
        #         status_date=status_date,
        #         created_by=self.request.user
        #     )
        # else:
        #     serializer.save(
        #         barrier=barrier_obj,
        #         status=barrier_status,
        #         summary=barrier_summary,
        #         status_date=status_date
        #     )


class BarrierResolve(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierResolveSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
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
        serializer.save(
            status=4,
            summary=self.request.data.get("summary"),
            status_date=self.request.data.get("status_date")
        )


class BarrierHibernate(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(serializer, self.kwargs.get("pk"), 5, self.request.data.get("summary"))


class BarrierOpen(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(serializer, self.kwargs.get("pk"), 2, self.request.data.get("summary"))
