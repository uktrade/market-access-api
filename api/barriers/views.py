import json
from collections import defaultdict
from dateutil.parser import parse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

import django_filters
from rest_framework.filters import OrderingFilter
from django_filters.fields import Lookup
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import (
    filters,
    generics,
    status,
    serializers,
    viewsets,
)
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.core.viewsets import CoreViewSet
from api.barriers.models import (
    BarrierInstance,
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
from api.interactions.models import Interaction

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
    barriers = BarrierInstance.barriers.all()
    reports = BarrierInstance.reports.all()
    if not current_user.is_anonymous:
        user_barrier_count = BarrierInstance.barriers.filter(
            created_by=current_user
        ).count()
        user_report_count = BarrierInstance.reports.filter(
            created_by=current_user
        ).count()
        user_count = {"barriers": user_barrier_count, "reports": user_report_count}
        if has_profile(current_user) and current_user.profile.location:
            country = current_user.profile.location
            country_barriers = barriers.filter(export_country=country)
            country_count = {
                "barriers": {
                    "total": country_barriers.count(),
                    "open": country_barriers.filter(status=2).count(),
                    "paused": country_barriers.filter(status=5).count(),
                    "resolved": country_barriers.filter(status=4).count(),
                },
                "reports": reports.filter(export_country=country).count(),
            }
            user_count["country"] = country_count

    counts = {
        "barriers": {
            "total": BarrierInstance.barriers.count(),
            "open": BarrierInstance.barriers.filter(status=2).count(),
            "paused": BarrierInstance.barriers.filter(status=5).count(),
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
    filter_backends = (OrderingFilter, )
    ordering_fields = ("created_on",)
    ordering = ("created_on",)

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
        serializer.save(created_by=self.request.user)
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
        Adds next_steps_summary, if exists, as a new note
        """
        # validate and submit a report
        report = self.get_object()
        barrier_obj = report.submit_report(self.request.user)
        # add next steps, if exists, as a new COMMENT note
        if barrier_obj.next_steps_summary is not None:
            kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
            Interaction(
                barrier=barrier_obj,
                text=barrier_obj.next_steps_summary,
                kind=kind,
                created_by=self.request.user,
            ).save()


class BarrierFilterSet(django_filters.FilterSet):
    """
    Custom FilterSet to handle all necessary filters on Barriers
    reported_on_before: filter start date dd-mm-yyyy
    reported_on_after: filter end date dd-mm-yyyy
    barrier_type: int, one or more comma seperated barrier type ids
        ex: barrier_type=1 or barrier_type=1,2
    sector: uuid, one or more comma seperated sector UUIDs
        ex:
        sector=af959812-6095-e211-a939-e4115bead28a
        sector=af959812-6095-e211-a939-e4115bead28a,9538cecc-5f95-e211-a939-e4115bead28a
    status: int, one or more status id's.
        ex: status=1 or status=1,2
    export_country: UUID, one or more comma seperated country UUIDs
        ex: 
        export_country=aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc
        export_country=aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc,955f66a0-5d95-e211-a939-e4115bead28a
    priority: priority code, one or more comma seperated priority codes
        ex: priority=UNKNOWN or priority=UNKNOWN,LOW
    """
    export_country = django_filters.BaseInFilter("export_country")
    reported_on = django_filters.DateFromToRangeFilter("reported_on")
    sector = django_filters.BaseInFilter(method="sector_filter")
    status = django_filters.BaseInFilter("status")
    barrier_type = django_filters.BaseInFilter("barrier_type")
    priority = django_filters.BaseInFilter(method="priority_filter")

    class Meta:
        model = BarrierInstance
        fields = [
            "export_country",
            "barrier_type",
            "sector",
            "reported_on",
            "status",
            "priority",
        ]

    def sector_filter(self, queryset, name, value):
        """
        custom filter to enable filtering Sectors, which is ArrayField
        """
        return queryset.filter(sectors__overlap=value)

    def priority_filter(self, queryset, name, value):
        priorities = BarrierPriority.objects.filter(code__in=value)
        if "UNKNOWN" in value:
            return queryset.filter(Q(priority__isnull=True) | Q(priority__in=priorities))
        else:
            return queryset.filter(priority__in=priorities)


class BarrierList(generics.ListAPIView):
    """
    Return a list of all the BarrierInstances with optional filtering.
    """

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("reported_on",)
    ordering = ("reported_on",)


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
        barrier = self.get_object()
        barrier_type = barrier.barrier_type
        if self.request.data.get("barrier_type", None) is not None:
            barrier_type = get_object_or_404(
                BarrierType, pk=self.request.data.get("barrier_type")
            )
        barrier_priority = barrier.priority
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
        timeline_fields = ["status", "priority"]
        barrier = BarrierInstance.barriers.get(id=pk)
        history = barrier.history.all().order_by("history_date")
        results = []
        old_record = None
        TIMELINE_REVERTED = {v: k for k, v in TIMELINE_EVENTS}
        for new_record in history:
            if new_record.history_type != "+":
                if old_record is not None:
                    status_change = None
                    delta = new_record.diff_against(old_record)
                    for change in delta.changes:
                        if change.field in timeline_fields:
                            if change.field == "status":
                                if not (change.old == 0 and (change.new == 2 or change.new == 4)):
                                    event = TIMELINE_REVERTED["Barrier Status Change"]
                                    status_change = {
                                        "date": new_record.history_date,
                                        "field": change.field,
                                        "old_value": str(change.old),
                                        "new_value": str(change.new),
                                        "user": self._username_from_user(
                                            new_record.history_user
                                        ),
                                        "field_info": {
                                            "status_date": new_record.status_date,
                                            "status_summary": new_record.status_summary,
                                            "event": event,
                                        }
                                    }
                            elif change.field == "priority":
                                status_change = {
                                    "date": new_record.history_date,
                                    "field": change.field,
                                    "old_value": str(change.old),
                                    "new_value": str(change.new),
                                    "user": self._username_from_user(
                                        new_record.history_user
                                    ),
                                    "field_info": {
                                        "priority_date": new_record.priority_date,
                                        "priority_summary": new_record.priority_summary,
                                    }
                                }
                    if status_change:
                        results.append(status_change)
            old_record = new_record
        response = {"barrier_id": str(pk), "history": results}
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
