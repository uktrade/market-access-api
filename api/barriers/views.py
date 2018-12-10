import json
from collections import defaultdict
from dateutil.parser import parse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import django_filters
from django_filters import Filter
from django_filters.fields import Lookup
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, status, serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.core.viewsets import CoreViewSet
from api.barriers.models import (
    BarrierInstance,
    BarrierInteraction,
    BarrierReportStage,
)
from api.barriers.serializers import (
    BarrierStaticStatusSerializer,
    BarrierInstanceSerializer,
    BarrierListSerializer,
    BarrierResolveSerializer,
    BarrierReportSerializer,
)
from api.metadata.constants import (
    BARRIER_INTERACTION_TYPE,
    BARRIER_STATUS,
    TIMELINE_EVENTS,
)

from api.metadata.models import (
    BarrierType,
    BarrierPriority
)

from api.user.utils import has_profile

UserModel = get_user_model()


@api_view(["GET"])
def barrier_count(request):
    """
    view to return number of barriers and reports in the system
    total counts, user counts, country counts and region counts
    {
        "barriers": 8,
        "reports": 6,
        "user": {
            "barriers": 1,
            "reports": 2,
            "country": {
                "barriers": 1,
                "reports": 0
            },
            "region": {
                "barriers": 1,
                "reports": 2
            }
        }
    }
    """
    current_user = request.user
    user_count = None
    if not current_user.is_anonymous:
        user_barrier_count = BarrierInstance.barriers.filter(
            created_by=current_user
        ).count()
        user_report_count = BarrierInstance.reports.filter(
            created_by=current_user
        ).count()
        user_count = {"barriers": user_barrier_count, "reports": user_report_count}
        country_barrier_count = None
        country_report_count = None
        country_count = None
        if has_profile(current_user) and current_user.profile.location:
            country = current_user.profile.location
            country_barrier_count = BarrierInstance.barriers.filter(
                export_country=country
            ).count()
            country_report_count = BarrierInstance.reports.filter(
                export_country=country
            ).count()
            country_count = {
                "barriers": country_barrier_count,
                "reports": country_report_count,
            }
            user_count["country"] = country_count

    counts = {
        "barriers": {
            "total": BarrierInstance.barriers.count(),
            "open": BarrierInstance.barriers.filter(status=2).count(),
            "resolved": BarrierInstance.barriers.filter(status=4).count(),
        },
        "reports": BarrierInstance.reports.count(),
    }
    if user_count:
        counts["user"] = user_count
    return Response(counts)


class BarrierReportBase(object):
    def _update_stages(self, serializer, user):
        report_id = serializer.data.get("id")
        report = BarrierInstance.reports.get(id=report_id)
        progress = report.current_progress()
        for new_stage, new_status in progress:
            try:
                report_stage = BarrierReportStage.objects.get(
                    barrier=report, stage=new_stage
                )
                report_stage.status = new_status
                report_stage.save()
            except BarrierReportStage.DoesNotExist:
                BarrierReportStage(
                    barrier=report, stage=new_stage, status=new_status
                ).save()
            if settings.DEBUG is False:
                report_stage = BarrierReportStage.objects.get(
                    barrier=report, stage=new_stage
                )
                report_stage.user = user
                report_stage.save()

    class Meta:
        abstract = True


class BarrierReportList(BarrierReportBase, generics.ListCreateAPIView):
    queryset = BarrierInstance.reports.all()
    serializer_class = BarrierReportSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned reports to a given export_country,
        by filtering against a `country` query parameter in the URL.
        and filtering against a `user` query parameter
        """
        queryset = BarrierInstance.reports.all()
        country = self.request.query_params.get("export_country", None)
        if country is not None:
            queryset = queryset.filter(export_country=country)
        return queryset

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
        """
        # validate and submit a report
        report = self.get_object()
        report.submit_report(self.request.user)


class BarrierFilterSet(django_filters.FilterSet):
    start_date = django_filters.DateFilter("status_date", lookup_expr="gte")
    end_date = django_filters.DateFilter("status_date", lookup_expr="lte")
    barrier_type = django_filters.ModelMultipleChoiceFilter(
        queryset=BarrierType.objects.all(), to_field_name="id", conjoined=True
    )
    sector = django_filters.UUIDFilter(method="sector_filter")

    class Meta:
        model = BarrierInstance
        fields = ["export_country", "barrier_type", "sector", "start_date", "end_date"]

    def sector_filter(self, queryset, name, value):
        """
        custom filter to enable filtering Sectors, which is ArrayField
        """
        return queryset.filter(sectors__contains=[value])


class BarrierList(generics.ListAPIView):
    """
    Return a list of all the BarrierInstances with optional filtering.
    """

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = BarrierFilterSet


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
        barrier_type = None
        if self.request.data.get("barrier_type", None) is not None:
            barrier_type = get_object_or_404(
                BarrierType, pk=self.request.data.get("barrier_type")
            )
        barrier_priority = None
        if self.request.data.get("priority", None) is not None:
            barrier_priority = get_object_or_404(
                BarrierPriority, code=self.request.data.get("priority")
            )

        serializer.save(
            barrier_type=barrier_type,
            priority=barrier_priority,
            modified_by=self.request.user
        )


class BarrierInstanceHistory(GenericAPIView):
    def _get_barrier(self, barrier_id):
        """ Get BarrierInstance object or False if invalid ID """
        try:
            return BarrierInstance.barriers.get(id=barrier_id)
        except BarrierInstance.DoesNotExist:
            return False

    def get(self, request, pk):
        ignore_fields = ["modified_on"]
        barrier = BarrierInstance.barriers.get(id=pk)
        history = barrier.history.all().order_by("history_date")
        results = []
        for new_record in history:
            if new_record.history_type == "+":
                results.append(
                    {
                        "date": new_record.history_date,
                        "operation": "Add",
                        "event": "Report created",
                        "field": None,
                        "old_value": None,
                        "new_value": None,
                        "user": new_record.history_user.email
                        if new_record.history_user
                        else "",
                    }
                )
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
                            event = "{} changed from {} to {}".format(
                                change.field, change.old, change.new
                            )
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
                                "user": new_record.history_user.email
                                if new_record.history_user
                                else "",
                            }
                        )
            old_record = new_record
            response = {"barrier_id": pk, "history": results}
        return Response(response, status=status.HTTP_200_OK)


class BarrierStatuseHistory(GenericAPIView):
    def _username_from_user(self, user):
        if user is not None:
            if user.username is not None and user.username.strip() != "":
                if "@" in user.username:
                    return {"id": user.id, "name": user.username.split("@")[0]}
                else:
                    return {"id": user.id, "name": user.username}
            elif user.email is not None and user.email.strip() != "":
                return user.email.split("@")[0]

        return None

    def get(self, request, pk):
        status_field = "status"
        barrier = BarrierInstance.barriers.get(id=pk)
        history = barrier.history.all().order_by("history_date")
        results = []
        old_record = None
        TIMELINE_REVERTED = {v: k for k, v in TIMELINE_EVENTS}
        for new_record in history:
            if new_record.history_type == "+":
                results.append(
                    {
                        "date": new_record.history_date,
                        "status_date": new_record.status_date,
                        "event": TIMELINE_REVERTED["Report Created"],
                        "old_status": None,
                        "new_status": new_record.status,
                        "status_summary": None,
                        "user": self._username_from_user(new_record.history_user),
                    }
                )
            else:
                if old_record is None:
                    results.append(
                        {
                            "date": new_record.history_date,
                            "status_date": new_record.status_date,
                            "event": TIMELINE_REVERTED["Barrier Status Change"],
                            "old_status": None,
                            "new_status": new_record.status,
                            "status_summary": new_record.status_summary,
                            "user": self._username_from_user(new_record.history_user),
                        }
                    )
                else:
                    status_change = None
                    delta = new_record.diff_against(old_record)
                    for change in delta.changes:
                        if change.field == status_field:
                            if change.old == 0 and (change.new == 2 or change.new == 4):
                                event = TIMELINE_REVERTED["Barrier Created"]
                            else:
                                event = TIMELINE_REVERTED["Barrier Status Change"]
                            status_change = {
                                "date": new_record.history_date,
                                "status_date": new_record.status_date,
                                "event": event,
                                "old_status": change.old,
                                "new_status": change.new,
                                "status_summary": new_record.status_summary,
                                "user": self._username_from_user(
                                    new_record.history_user
                                ),
                            }
                    if status_change:
                        results.append(status_change)
            old_record = new_record
            response = {"barrier_id": pk, "status_history": results}
        return Response(response, status=status.HTTP_200_OK)


class BarrierStatusBase(generics.UpdateAPIView):
    def _create(
        self, serializer, barrier_id, barrier_status, barrier_summary, status_date=None
    ):
        barrier_obj = get_object_or_404(BarrierInstance, pk=barrier_id)

        if status_date is None:
            status_date = timezone.now()

        serializer.save(
            status=barrier_status,
            status_summary=barrier_summary,
            status_date=status_date,
            modified_by=self.request.user,
        )


class BarrierResolve(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierResolveSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        errors = defaultdict(list)
        if self.request.data.get("status_summary", None) is None:
            errors["status_summary"] = "This field is required"
        if self.request.data.get("status_date", None) is None:
            errors["status_date"] = "This field is required"
        else:
            try:
                parse(self.request.data.get("status_date"))
            except ValueError:
                errors["status_date"] = "enter a valid date"
        if errors:
            message = {"fields": errors}
            raise serializers.ValidationError(message)
        serializer.save(
            status=4,
            status_summary=self.request.data.get("status_summary"),
            status_date=self.request.data.get("status_date"),
            modified_by=self.request.user,
        )


class BarrierHibernate(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer,
            self.kwargs.get("pk"),
            5,
            self.request.data.get("status_summary"),
        )


class BarrierOpen(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer,
            self.kwargs.get("pk"),
            2,
            self.request.data.get("status_summary"),
        )
