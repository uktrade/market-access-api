import csv
import datetime
from collections import defaultdict

from django.db import transaction
from django.db.models import Count
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now

from dateutil.parser import parse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, serializers, status, mixins
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from simple_history.utils import bulk_create_with_history

from api.barriers.csv import create_csv_response
from api.barriers.history import (
    AssessmentHistoryFactory,
    BarrierHistoryFactory,
    NoteHistoryFactory,
    TeamMemberHistoryFactory,
    WTOHistoryFactory,
)
from api.barriers.models import BarrierInstance, BarrierReportStage, PublicBarrier
from api.barriers.serializers import (
    BarrierCsvExportSerializer,
    BarrierInstanceSerializer,
    BarrierListSerializer,
    BarrierReportSerializer,
    BarrierResolveSerializer,
    BarrierStaticStatusSerializer,
    PublicBarrierSerializer,
)
from api.collaboration.mixins import TeamMemberModelMixin
from api.collaboration.models import TeamMember
from api.core.utils import cleansed_username
from api.interactions.models import Interaction
from api.metadata.constants import BARRIER_INTERACTION_TYPE, TIMELINE_EVENTS, PublicBarrierStatus
from api.metadata.models import BarrierPriority, Category
from api.user.helpers import has_profile, update_user_profile
from api.user.models import get_my_barriers_saved_search, get_team_barriers_saved_search
from api.user.models import Profile, SavedSearch
from api.user_event_log.constants import USER_EVENT_TYPES
from api.user_event_log.utils import record_user_event
from .filters import BarrierFilterSet


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
        user = self.request.user
        barrier_obj = report.submit_report(user)

        # add next steps, if exists, as a new COMMENT note
        if barrier_obj.next_steps_summary is not None:
            kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
            Interaction(
                barrier=barrier_obj,
                text=barrier_obj.next_steps_summary,
                kind=kind,
                created_by=user,
            ).save()

        Profile.objects.get_or_create(user=user)
        if user.profile.sso_user_id is None:
            update_user_profile(user, self.request.auth.token)

        # Create default team members
        new_members = (
            TeamMember(barrier=barrier_obj, user=user, role=TeamMember.REPORTER, default=True),
            TeamMember(barrier=barrier_obj, user=user, role=TeamMember.OWNER, default=True),
        )
        # using a helper here due to - https://django-simple-history.readthedocs.io/en/2.8.0/common_issues.html
        bulk_create_with_history(new_members, TeamMember)


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

    def is_my_barriers_search(self):
        if self.request.GET.get("user") == "1":
            return True
        return False

    def is_team_barriers_search(self):
        if self.request.GET.get("team") == "1":
            return True
        return False

    def get_saved_search(self, search_id):
        try:
            return SavedSearch.objects.get(pk=search_id, user=self.request.user)
        except SavedSearch.DoesNotExist:
            pass

    def update_saved_search_if_required(self):
        search_id = self.request.GET.get("search_id")
        query_dict = self.request.query_params.dict()

        if search_id:
            saved_search = self.get_saved_search(search_id)
            if saved_search and saved_search.are_api_parameters_equal(query_dict):
                saved_search.mark_as_seen()

        if self.is_my_barriers_search():
            saved_search = get_my_barriers_saved_search(self.request.user)
            if saved_search.are_api_parameters_equal(query_dict):
                saved_search.mark_as_seen()

        if self.is_team_barriers_search():
            saved_search = get_team_barriers_saved_search(self.request.user)
            if saved_search.are_api_parameters_equal(query_dict):
                saved_search.mark_as_seen()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.update_saved_search_if_required()
        return response


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


class BarrierDetail(TeamMemberModelMixin, generics.RetrieveUpdateAPIView):
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
        # Update Categories
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
        # Update Priority
        barrier_priority = barrier.priority
        if self.request.data.get("priority", None) is not None:
            barrier_priority = get_object_or_404(
                BarrierPriority, code=self.request.data.get("priority")
            )
        # Update Team members
        self.update_contributors(barrier)
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

    def get(self, request, pk):     # noqa: C901
        # TODO: refactor to remove complexity
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
        elif (
            self.request.data.get("sub_status", None) == "OTHER"
            and self.request.data.get("sub_status_other", None) is None
        ):
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


class PublicBarrierViewSet(mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           GenericViewSet):
    """
    Manage public data for barriers.
    """
    barriers_qs = BarrierInstance.barriers.all()
    http_method_names = ["get", "post", "patch",  "head", "options"]

    def get_serializer_class(self):
        # TODO: do the validation, sifters should have a
        #       restricted serializer that only allows them to read public barriers
        # if self.request.user.is_sifter:
        #     return ReadOnlyPublicBarrierSerializer
        return PublicBarrierSerializer

    def get_object(self):
        barrier = get_object_or_404(self.barriers_qs, pk=self.kwargs.get("pk"))
        public_barrier, created = PublicBarrier.objects.get_or_create(
            barrier=barrier,
            defaults={
                "status": barrier.status,
                "country": barrier.export_country,
                "sectors": barrier.sectors,
            }
        )
        if created:
            public_barrier.categories.set(barrier.categories.all())
        # TODO: is there a need to flag if there are changes for fields that cannot be edited?
        # else:
        #     if public_barrier.modified_on < barrier.modified_on:
        #         public_barrier.status = barrier.status
        #         public_barrier.country = barrier.export_country
        #         public_barrier.sectors = barrier.sectors
        #         public_barrier.save()
        #         public_barrier.categories.set(barrier.categories.all())

        return public_barrier

    # TODO: add permission classes to restrict this action to Publishers
    @action(methods=["post"], detail=True)
    def publish(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    # TODO: add permission classes to restrict this action to Publishers
    @action(methods=["post"], detail=True)
    def unpublish(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        public_barrier.public_view_status = PublicBarrierStatus.UNPUBLISHED
        public_barrier.save()
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)
