import csv
import datetime
from collections import defaultdict
from dateutil.parser import parse

from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now

import django_filters
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.widgets import BooleanWidget

from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.barriers.csv import create_csv_response
from api.core.utils import cleansed_username
from api.barriers.history import (
    AssessmentHistoryFactory,
    BarrierHistoryFactory,
    NoteHistoryFactory,
    TeamMemberHistoryFactory,
    WTOHistoryFactory,
)
from api.barriers.models import BarrierInstance, BarrierReportStage
from api.barriers.serializers import (
    BarrierStaticStatusSerializer,
    BarrierInstanceSerializer,
    BarrierCsvExportSerializer,
    BarrierListSerializer,
    BarrierResolveSerializer,
    BarrierReportSerializer,
)
from api.metadata.constants import (
    BARRIER_INTERACTION_TYPE,
    TIMELINE_EVENTS,
)

from api.metadata.models import Category, BarrierPriority
from api.metadata.utils import get_countries

from api.interactions.models import Interaction
from api.collaboration.models import TeamMember

from api.user.utils import has_profile

from api.user_event_log.constants import USER_EVENT_TYPES
from api.user_event_log.utils import record_user_event
from api.user.models import Profile, SavedSearch
from api.user.staff_sso import StaffSSO

UserModel = get_user_model()
sso = StaffSSO()


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

@api_view(["GET"])
def barriers_export(request):
    """A view that streams a large CSV file."""
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    barriers = BarrierInstance.barriers.all()

    rows = ([barrier.id, barrier.export_country] for barrier in barriers)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in rows),
        content_type="text/csv"
    )
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    return response

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
    serializer_class = BarrierReportSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_on",)
    ordering = ("created_on",)

    def get_queryset(self):
        """
        This view should return a list of all the reports
        for the currently authenticated user.
        """
        queryset = BarrierInstance.reports.all()
        user = self.request.user
        return queryset.filter(created_by=user)

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        self._update_stages(serializer, self.request.user)


class BarrierReportDetail(BarrierReportBase, generics.RetrieveUpdateDestroyAPIView):

    lookup_field = "pk"
    queryset = BarrierInstance.reports.all()
    serializer_class = BarrierReportSerializer

    @transaction.atomic()
    def perform_update(self, serializer):
        serializer.save()
        self._update_stages(serializer, self.request.user)

    def perform_destroy(self, instance):
        if int(instance.created_by.id) == int(self.request.user.id):
            instance.archive(self.request.user)
            return
        raise PermissionDenied()


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
        # add submitted_by as default team member
        try:
            profile = self.request.user.profile
        except Profile.DoesNotExist:
            Profile.objects.create(user=self.request.user)

        if self.request.user.profile.sso_user_id is None:
            token = self.request.auth.token
            context = {"token": token}
            sso_user = sso.get_logged_in_user_details(context)
            self.request.user.username = sso_user["email"]
            self.request.user.email = sso_user["contact_email"]
            self.request.user.first_name = sso_user["first_name"]
            self.request.user.last_name = sso_user["last_name"]
            self.request.user.save()
            self.request.user.profile.sso_user_id = sso_user["user_id"]
            self.request.user.profile.save()
        TeamMember(
            barrier=barrier_obj,
            user=self.request.user,
            role='Reporter',
            default=True
        ).save()


class BarrierFilterSet(django_filters.FilterSet):
    """
    Custom FilterSet to handle all necessary filters on Barriers
    reported_on_before: filter start date dd-mm-yyyy
    reported_on_after: filter end date dd-mm-yyyy
    cateogory: int, one or more comma seperated category ids
        ex: category=1 or category=1,2
    sector: uuid, one or more comma seperated sector UUIDs
        ex:
        sector=af959812-6095-e211-a939-e4115bead28a
        sector=af959812-6095-e211-a939-e4115bead28a,9538cecc-5f95-e211-a939-e4115bead28a
    status: int, one or more status id's.
        ex: status=1 or status=1,2
    location: UUID, one or more comma seperated overseas region/country/state UUIDs
        ex:
        location=aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc
        location=aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc,955f66a0-5d95-e211-a939-e4115bead28a
    priority: priority code, one or more comma seperated priority codes
        ex: priority=UNKNOWN or priority=UNKNOWN,LOW
    text: combination custom search across multiple fields.
        Searches for reference code,
        barrier title and barrier summary
    """

    reported_on = django_filters.DateFromToRangeFilter("reported_on")
    sector = django_filters.BaseInFilter(method="sector_filter")
    status = django_filters.BaseInFilter("status")
    barrier_type = django_filters.BaseInFilter("categories")
    category = django_filters.BaseInFilter("categories")
    priority = django_filters.BaseInFilter(method="priority_filter")
    location = django_filters.Filter(method="location_filter")
    text = django_filters.Filter(method="text_search")
    user = django_filters.Filter(method="my_barriers")
    team = django_filters.Filter(method="team_barriers")
    archived = django_filters.BooleanFilter("archived", widget=BooleanWidget)
    tags = django_filters.Filter(method="tags_filter")
    trade_direction = django_filters.BaseInFilter("trade_direction")

    wto_has_been_notified = django_filters.BooleanFilter(
        "wto_has_been_notified",
        method="wto_has_been_notified_filter",
        widget=BooleanWidget,
    )
    wto_should_be_notified = django_filters.BooleanFilter(
        "wto_should_be_notified",
        method="wto_should_be_notified_filter",
        widget=BooleanWidget,
    )
    has_wto_raised_date = django_filters.BooleanFilter(
        "has_wto_raised_date",
        method="has_wto_raised_date_filter",
        widget=BooleanWidget,
    )
    has_wto_committee_raised_in = django_filters.BooleanFilter(
        "has_wto_committee_raised_in",
        method="has_wto_committee_raised_in_filter",
        widget=BooleanWidget,
    )
    has_wto_case_number = django_filters.BooleanFilter(
        "has_wto_case_number",
        method="has_wto_case_number_filter",
        widget=BooleanWidget,
    )
    has_wto_profile = django_filters.BooleanFilter(
        "has_wto_profile",
        method="has_wto_profile_filter",
        widget=BooleanWidget,
    )

    class Meta:
        model = BarrierInstance
        fields = [
            "export_country",
            "barrier_type",
            "category",
            "sector",
            "reported_on",
            "status",
            "priority",
            "archived",
        ]

    def sector_filter(self, queryset, name, value):
        """
        custom filter for multi-select filtering of Sectors field,
        which is ArrayField
        """
        return queryset.filter(
            Q(all_sectors=True) | Q(sectors__overlap=value)
        )

    def priority_filter(self, queryset, name, value):
        """
        customer filter for multi-select of priorities field
        by code rather than priority id.
        UNKNOWN would either mean, UNKNOWN is set in the field
        or priority is not yet set for that barrier
        """
        UNKNOWN = "UNKNOWN"
        priorities = BarrierPriority.objects.filter(code__in=value)
        if UNKNOWN in value:
            return queryset.filter(
                Q(priority__isnull=True) | Q(priority__in=priorities)
            )
        else:
            return queryset.filter(priority__in=priorities)

    def location_filter(self, queryset, name, value):
        """
        custom filter for retreiving barriers of all countries of an overseas region
        """
        countries = cache.get_or_set("dh_countries", get_countries, 72000)
        items = value.split(',')
        countries_for_region = [
            item["id"]
            for item in countries
            if item["overseas_region"] and item["overseas_region"]["id"] in items
        ]
        return queryset.filter(
            Q(export_country__in=items) |
            Q(export_country__in=countries_for_region) |
            Q(country_admin_areas__overlap=items)
        )

    def text_search(self, queryset, name, value):
        """
        custom text search against multiple fields
            full value of code
            full text search on summary
            partial search on barrier_title
        """
        return queryset.annotate(
            search=SearchVector('summary')
        ).filter(
            Q(code=value) | Q(search=value) | Q(barrier_title__icontains=value)
        )

    def my_barriers(self, queryset, name, value):
        if value:
            current_user = self.request.user
            qs = queryset.filter(created_by=current_user)
            return qs
        return queryset

    def team_barriers(self, queryset, name, value):
        if value:
            current_user = self.request.user
            return queryset.filter(
                Q(barrier_team__user=current_user) & Q(barrier_team__archived=False)
            ).distinct()
        return queryset

    def tags_filter(self, queryset, name, value):
        if isinstance(value, str):
            tag_ids = value.split(",")
        else:
            tag_ids = value
        return queryset.filter(tags__in=tag_ids).distinct()

    def wto_has_been_notified_filter(self, queryset, name, value):
        return queryset.filter(wto_profile__wto_has_been_notified=value)

    def wto_should_be_notified_filter(self, queryset, name, value):
        return queryset.filter(wto_profile__wto_should_be_notified=value)

    def has_wto_raised_date_filter(self, queryset, name, value):
        return queryset.filter(wto_profile__raised_date__isnull=not value)

    def has_wto_committee_raised_in_filter(self, queryset, name, value):
        return queryset.filter(wto_profile__committee_raised_in__isnull=not value)

    def has_wto_case_number_filter(self, queryset, name, value):
        if value is True:
            return queryset.filter(
                wto_profile__isnull=False
            ).exclude(wto_profile__case_number="")
        return queryset

    def has_wto_profile_filter(self, queryset, name, value):
        return queryset.filter(wto_profile__isnull=not value)


class BarrierList(generics.ListAPIView):
    """
    Return a list of all the BarrierInstances
    with optional filtering and ordering defined
    """

    queryset = BarrierInstance.barriers.all().select_related('priority')
    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = (
        "reported_on",
        "modified_on",
        "status",
        "priority",
        "export_country"
    )
    ordering = ("reported_on", "modified_on")

    def update_saved_search(self, search_id, barriers):
        try:
            saved_search = SavedSearch.objects.get(pk=search_id, user=self.request.user)
        except SavedSearch.DoesNotExist:
            return

        saved_search.last_viewed_on = datetime.datetime.utcnow()
        saved_search.last_viewed_barrier_ids = [barrier["id"] for barrier in barriers]
        saved_search.save()

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        search_id = self.request.GET.get("search_id")
        if search_id:
            self.update_saved_search(search_id, serializer.data)
        return serializer


class BarriertListExportView(generics.ListAPIView):
    """
    Return a streaming http response of all the BarrierInstances
    with optional filtering and ordering defined
    """

    queryset = BarrierInstance.barriers.annotate(
        team_count=Count('barrier_team')
    ).all().select_related("assessment").select_related(
        "wto_profile__committee_notified"
    ).select_related(
        "wto_profile__committee_raised_in"
    ).select_related(
        "priority"
    ).prefetch_related("tags").prefetch_related("categories")
    serializer_class = BarrierCsvExportSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    field_titles = {
            "id": "id",
            "code": "code",
            "barrier_title": "Title",
            "status": "Status",
            "priority": "Priority",
            "overseas_region": "Overseas Region",
            "country": "Country",
            "admin_areas": "Admin areas",
            "sectors": "Sectors",
            "product": "Product",
            "scope": "Scope",
            "categories": "Barrier categories",
            "source": "Source",
            "team_count": "Team count",
	        "assessment_impact": "Assessment Impact",
	        "value_to_economy": "Value to economy",
	        "import_market_size": "Import market size",
	        "commercial_value": "Commercial Value",
	        "export_value": "Value of currently affected UK exports",
            "reported_on": "Reported Date",
            "status_date": "Status Date",
            "modified_on": "Last updated",
            "tags": "Tags",
            "trade_direction": "Trade direction",
            "end_date": "End date",
            "summary": "Summary",
            "link": "Link",
            "economic_assessment_explanation": "Economic assessment",
            "wto_has_been_notified": "WTO Notified",
            "wto_should_be_notified": "WTO Should Notify",
            "wto_committee_notified": "WTO Committee Notified",
            "wto_committee_notification_link": "WTO Committee Notified Link",
            "wto_member_states": "WTO Raised Members",
            "wto_committee_raised_in": "WTO Raised Committee",
            "wto_raised_date": "WTO Raised Date",
            "wto_case_number": "WTO Case Number",
        }

    def _get_rows(self, queryset):
        """
        Returns an iterable using QuerySet.iterator() over the search results.
        """

        return queryset.values(
            *self.field_titles.keys(),
        ).iterator()

    def _get_base_filename(self):
        """
        Gets the filename (without the .csv suffix) for the CSV file download.
        """
        filename_parts = [
            'Data Hub Market Access Barriers',
            now().strftime('%Y-%m-%d-%H-%M-%S'),
        ]
        return ' - '.join(filename_parts)

    def get(self, request, *args, **kwargs):
        """
        Returns CSV file with all search results for barriers
        """
        user_event_data = {}

        record_user_event(request, USER_EVENT_TYPES.csv_download, data=user_event_data)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        base_filename = self._get_base_filename()
        return create_csv_response(serializer.data, self.field_titles, base_filename)


class BarrierDetail(generics.RetrieveUpdateAPIView):
    """
    Return details of a BarrierInstance
    Allows the barrier to be updated as well
    """

    lookup_field = "pk"
    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierInstanceSerializer

    def get_object(self):
        if "code" in self.kwargs:
            self.lookup_url_kwarg = "code"
            self.lookup_field = "code"
        return super().get_object()

    @transaction.atomic()
    def perform_update(self, serializer):
        barrier = self.get_object()
        categories = barrier.categories.all()
        category_ids = self.request.data.get(
            "barrier_types",
            self.request.data.get("categories", None)
        )
        if category_ids is not None:
            categories = [
                get_object_or_404(Category, pk=category_id)
                for category_id in category_ids
            ]
        barrier_priority = barrier.priority
        if self.request.data.get("priority", None) is not None:
            barrier_priority = get_object_or_404(
                BarrierPriority, code=self.request.data.get("priority")
            )

        serializer.save(
            categories=categories,
            priority=barrier_priority,
            modified_by=self.request.user,
        )


class HistoryMixin:
    """
    Mixin for getting barrier history items
    """

    def get_assessment_history(self, fields=(), start_date=None):
        return AssessmentHistoryFactory.get_history_items(
            barrier_id=self.kwargs.get("pk"),
            fields=fields,
            start_date=start_date,
        )

    def get_barrier_history(self, fields=(), start_date=None):
        return BarrierHistoryFactory.get_history_items(
            barrier_id=self.kwargs.get("pk"),
            fields=fields,
            start_date=start_date,
        )

    def get_notes_history(self, fields=(), start_date=None):
        return NoteHistoryFactory.get_history_items(
            barrier_id=self.kwargs.get("pk"),
            fields=fields,
            start_date=start_date,
        )

    def get_team_history(self, fields=(), start_date=None):
        return TeamMemberHistoryFactory.get_history_items(
            barrier_id=self.kwargs.get("pk"),
            fields=fields,
            start_date=start_date,
        )

    def get_wto_history(self, fields=(), start_date=None):
        return WTOHistoryFactory.get_history_items(
            barrier_id=self.kwargs.get("pk"),
            fields=fields,
            start_date=start_date,
        )


class BarrierFullHistory(HistoryMixin, generics.GenericAPIView):
    """
    Full audit history of changes made to a barrier and related models
    """

    def get(self, request, pk):
        barrier = BarrierInstance.objects.get(id=self.kwargs.get("pk"))

        barrier_history = self.get_barrier_history(start_date=barrier.reported_on)
        notes_history = self.get_notes_history(start_date=barrier.reported_on)
        assessment_history = self.get_assessment_history(start_date=barrier.reported_on)
        team_history = self.get_team_history(
            start_date=barrier.reported_on + datetime.timedelta(seconds=1)
        )
        wto_history = self.get_wto_history(start_date=barrier.reported_on)

        history_items = (
            barrier_history + notes_history + assessment_history + team_history
            + wto_history
        )

        response = {
            "barrier_id": str(pk),
            "history": [item.data for item in history_items],
        }
        return Response(response, status=status.HTTP_200_OK)


class BarrierActivity(HistoryMixin, generics.GenericAPIView):
    """
    Returns history items used on the barrier activity stream

    This will supersede the BarrierStatusHistory view below.
    """

    def get(self, request, pk):
        barrier_history = self.get_barrier_history(
            fields=["archived", "priority", "status"],
        )
        assessment_history = self.get_assessment_history(
            fields=[
                "commercial_value",
                "export_value",
                "impact",
                "import_market_size",
                "value_to_economy",
            ]
        )

        history_items = barrier_history + assessment_history

        response = {
            "barrier_id": str(pk),
            "history": [item.data for item in history_items],
        }
        return Response(response, status=status.HTTP_200_OK)


class BarrierStatusHistory(generics.GenericAPIView):
    """
    Returns history items used on the barrier activity stream

    This will be deprecated in favour of the BarrierActivity view above.
    """

    def _format_user(self, user):
        if user is not None:
            return {"id": user.id, "name": cleansed_username(user)}

        return None

    def get(self, request, pk):
        status_field = "status"
        timeline_fields = ["status", "priority", "archived"]
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
                                # ignore default status setup, during report submission
                                if not (change.old == 0 or change.old is None):
                                    event = TIMELINE_REVERTED["Barrier Status Change"]
                                    status_change = {
                                        "date": new_record.history_date,
                                        "model": "barrier",
                                        "field": change.field,
                                        "old_value": str(change.old),
                                        "new_value": str(change.new),
                                        "user": self._format_user(
                                            new_record.history_user
                                        ),
                                        "field_info": {
                                            "status_date": new_record.status_date,
                                            "status_summary": new_record.status_summary,
                                            "sub_status": new_record.sub_status,
                                            "sub_status_other": new_record.sub_status_other,
                                            "event": event,
                                        },
                                    }
                            elif change.field == "priority":
                                status_change = {
                                    "date": new_record.history_date,
                                    "model": "barrier",
                                    "field": change.field,
                                    "old_value": str(change.old),
                                    "new_value": str(change.new),
                                    "user": self._format_user(
                                        new_record.history_user
                                    ),
                                    "field_info": {
                                        "priority_date": new_record.priority_date,
                                        "priority_summary": new_record.priority_summary,
                                    },
                                }
                            elif change.field == "archived":
                                status_change = {
                                    "date": new_record.history_date,
                                    "model": "barrier",
                                    "field": change.field,
                                    "old_value": change.old,
                                    "new_value": change.new,
                                    "user": self._format_user(
                                        new_record.history_user
                                    ),
                                }
                                if change.new is True:
                                    status_change["field_info"] = {
                                        "archived_reason": new_record.archived_reason,
                                        "archived_explanation": new_record.archived_explanation,
                                    }
                                else:
                                    status_change["field_info"] = {
                                        "unarchived_reason": new_record.unarchived_reason,
                                    }
                    if status_change:
                        results.append(status_change)
            old_record = new_record
        response = {"barrier_id": str(pk), "history": results}

        return Response(response, status=status.HTTP_200_OK)


class BarrierStatusBase(generics.UpdateAPIView):
    def _create(
        self, serializer, barrier_id, status, summary, sub_status=None, sub_other=None, status_date=None
    ):
        barrier_obj = get_object_or_404(BarrierInstance, pk=barrier_id)

        if status_date is None:
            status_date = timezone.now().date()

        serializer.save(
            status=status,
            sub_status=sub_status,
            sub_status_other=sub_other,
            status_summary=summary,
            status_date=status_date,
            modified_by=self.request.user,
        )


class BarrierResolveInFull(BarrierStatusBase):

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
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=4,
            summary=self.request.data.get("status_summary"),
            status_date=self.request.data.get("status_date")
        )


class BarrierResolveInPart(BarrierStatusBase):

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
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=3,
            summary=self.request.data.get("status_summary"),
            status_date=self.request.data.get("status_date")
        )


class BarrierHibernate(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=5,
            summary=self.request.data.get("status_summary"),
        )


class BarrierStatusChangeUnknown(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=7,
            summary=self.request.data.get("status_summary"),
        )


class BarrierOpenInProgress(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=2,
            summary=self.request.data.get("status_summary"),
        )


class BarrierOpenActionRequired(BarrierStatusBase):

    queryset = BarrierInstance.barriers.all()
    serializer_class = BarrierStaticStatusSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        errors = defaultdict(list)
        if self.request.data.get("sub_status", None) is None:
            errors["sub_status"] = "This field is required"
        elif self.request.data.get("sub_status", None) == "OTHER" and self.request.data.get("sub_status_other", None) is None:
            errors["sub_status_other"] = "This field is required"
        if self.request.data.get("status_summary", None) is None:
            errors["status_summary"] = "This field is required"

        if errors:
            message = {"fields": errors}
            raise serializers.ValidationError(message)
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=1,
            sub_status=self.request.data.get("sub_status"),
            sub_other=self.request.data.get("sub_status_other"),
            summary=self.request.data.get("status_summary"),
            status_date=self.request.data.get("status_date")
        )
