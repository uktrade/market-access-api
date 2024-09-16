import csv
import logging
from collections import defaultdict
from datetime import datetime

from dateutil.parser import parse
from django.db import transaction
from django.db.models import (
    Case,
    CharField,
    F,
    IntegerField,
    Prefetch,
    Q,
    Sum,
    Value,
    When,
)
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, serializers, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from simple_history.utils import bulk_create_with_history

from api.barriers import barrier_cache
from api.barriers.exceptions import PublicBarrierPublishException
from api.barriers.helpers import get_or_create_public_barrier
from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierReportStage,
    BarrierTopPrioritySummary,
    ProgrammeFundProgressUpdate,
    PublicBarrier,
)
from api.barriers.serializers import (
    BarrierDetailSerializer,
    BarrierListSerializer,
    BarrierReportSerializer,
    PublicBarrierSerializer,
)
from api.barriers.serializers.csv import BarrierRequestDownloadApprovalSerializer
from api.barriers.serializers.priority_summary import PrioritySummarySerializer
from api.barriers.serializers.progress_updates import (
    NextStepItemSerializer,
    ProgrammeFundProgressUpdateSerializer,
    ProgressUpdateSerializer,
)
from api.collaboration.mixins import TeamMemberModelMixin
from api.collaboration.models import TeamMember
from api.history.manager import HistoryManager
from api.interactions.models import Interaction
from api.metadata.constants import (
    BARRIER_INTERACTION_TYPE,
    BARRIER_SEARCH_ORDERING_CHOICES,
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC_LOOKUP,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.user.helpers import has_profile
from api.user.models import (
    SavedSearch,
    get_my_barriers_saved_search,
    get_team_barriers_saved_search,
)
from api.user.permissions import AllRetrieveAndEditorUpdateOnly, IsApprover, IsPublisher

from .models import BarrierFilterSet, BarrierProgressUpdate, PublicBarrierFilterSet
from .public_data import public_release_to_s3

logger = logging.getLogger(__name__)


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
    barriers = Barrier.barriers.all()

    rows = ([barrier.id, barrier.country] for barrier in barriers)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in rows), content_type="text/csv"
    )
    response["Content-Disposition"] = 'attachment; filename="somefilename.csv"'
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
    barriers = Barrier.barriers.all()
    reports = Barrier.reports.all()
    if not current_user.is_anonymous:
        user_barrier_count = Barrier.barriers.filter(created_by=current_user).count()
        user_report_count = Barrier.reports.filter(created_by=current_user).count()
        user_count = {"barriers": user_barrier_count, "reports": user_report_count}
        if has_profile(current_user) and current_user.profile.location:
            country = current_user.profile.location
            country_barriers = barriers.filter(country=country)
            country_count = {
                "barriers": {
                    "total": country_barriers.count(),
                    "open": country_barriers.filter(status=2).count(),
                    "paused": country_barriers.filter(status=5).count(),
                    "resolved": country_barriers.filter(status=4).count(),
                },
                "reports": reports.filter(country=country).count(),
            }
            user_count["country"] = country_count

    counts = {
        "barriers": {
            "total": Barrier.barriers.count(),
            "open": Barrier.barriers.filter(status=2).count(),
            "paused": Barrier.barriers.filter(status=5).count(),
            "resolved": Barrier.barriers.filter(status=4).count(),
        },
        "reports": Barrier.reports.count(),
    }
    if user_count:
        counts["user"] = user_count
    return Response(counts)


class BarrierReportBase(object):
    def _update_stages(self, serializer, user):
        report_id = serializer.data.get("id")
        report = Barrier.reports.get(id=report_id)
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


class BarrierDashboardSummary(generics.GenericAPIView):
    """
    View to return high level stats to the dashboard
    """

    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet

    filter_backends = (DjangoFilterBackend,)
    ordering_fields = (
        "reported_on",
        "modified_on",
        "estimated_resolution_date",
        "status",
        "priority",
        "country",
    )
    ordering = ("-reported_on",)

    def get(self, request):
        filtered_queryset = self.filter_queryset(
            Barrier.barriers.filter(archived=False)
        )

        current_user = self.request.user

        # Get current financial year
        current_year_start = datetime(datetime.now().year, 4, 1)
        current_year_end = datetime(datetime.now().year + 1, 3, 31)
        previous_year_start = datetime(datetime.now().year - 1, 4, 1)
        previous_year_end = datetime(datetime.now().year + 1, 3, 31)

        if not current_user.is_anonymous:
            user_barrier_count = Barrier.barriers.filter(
                created_by=current_user
            ).count()
            user_report_count = Barrier.reports.filter(created_by=current_user).count()
            user_open_barrier_count = Barrier.barriers.filter(
                created_by=current_user, status=2
            ).count()

        when_assessment = [
            When(valuation_assessments__impact=k, then=Value(v))
            for k, v in ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC_LOOKUP
        ]

        # Resolved vs Estimated barriers values chart
        resolved_valuations = (
            filtered_queryset.filter(
                Q(
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ]
                )
                | Q(
                    status_date__range=[
                        current_year_start,
                        current_year_end,
                    ]
                ),
                Q(status=4) | Q(status=3),
                valuation_assessments__archived=False,
            )
            .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
            .aggregate(total=Sum("numeric_value"))
        )

        resolved_barrier_value = resolved_valuations["total"]

        estimated_valuations = (
            filtered_queryset.filter(
                Q(
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ]
                )
                | Q(
                    status_date__range=[
                        current_year_start,
                        current_year_end,
                    ]
                ),
                Q(status=1) | Q(status=2),
                valuation_assessments__archived=False,
            )
            .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
            .aggregate(total=Sum("numeric_value"))
        )

        estimated_barrier_value = estimated_valuations["total"]

        # Total resolved barriers vs open barriers value chart

        resolved_barriers = (
            filtered_queryset.filter(
                Q(status=4) | Q(status=3),
                valuation_assessments__archived=False,
            )
            .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
            .aggregate(total=Sum("numeric_value"))
        )

        total_resolved_barriers = resolved_barriers["total"]

        open_barriers = (
            filtered_queryset.filter(
                Q(status=1) | Q(status=2),
                valuation_assessments__archived=False,
            )
            .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
            .aggregate(total=Sum("numeric_value"))
        )

        open_barriers_value = open_barriers["total"]

        # Open barriers by status
        whens = [When(status=k, then=Value(v)) for k, v in BarrierStatus.choices]

        barrier_by_status = (
            filtered_queryset.filter(
                valuation_assessments__archived=False,
            )
            .annotate(status_display=Case(*whens, output_field=CharField()))
            .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
            .values("status_display")
            .annotate(total=Sum("numeric_value"))
            .order_by()
        )

        status_labels = []
        status_data = []

        for series in barrier_by_status:
            status_labels.append(series["status_display"])
            status_data.append(series["total"])

        # TODO for status filter might need to consider status dates as well as ERD
        counts = {
            "financial_year": {
                "current_start": current_year_start,
                "current_end": current_year_end,
                "previous_start": previous_year_start,
                "previous_end": previous_year_end,
            },
            "barriers": {
                "total": filtered_queryset.count(),
                "open": filtered_queryset.filter(status=2).count(),
                "paused": filtered_queryset.filter(status=5).count(),
                "resolved": filtered_queryset.filter(status=4).count(),
                "pb100": filtered_queryset.filter(
                    top_priority_status="Approved"
                ).count(),
                "overseas_delivery": filtered_queryset.filter(
                    priority_level="OVERSEAS"
                ).count(),
            },
            "barriers_current_year": {
                "total": filtered_queryset.filter(
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ]
                ).count(),
                "open": filtered_queryset.filter(
                    status=2,
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ],
                ).count(),
                "paused": filtered_queryset.filter(
                    status=5,
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ],
                ).count(),
                "resolved": filtered_queryset.filter(
                    status=4,
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ],
                ).count(),
                "pb100": filtered_queryset.filter(
                    top_priority_status="Approved",
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ],
                ).count(),
                "overseas_delivery": filtered_queryset.filter(
                    priority_level="OVERSEAS",
                    estimated_resolution_date__range=[
                        current_year_start,
                        current_year_end,
                    ],
                ).count(),
            },
            "user_counts": {
                "user_barrier_count": user_barrier_count,
                "user_report_count": user_report_count,
                "user_open_barrier_count": user_open_barrier_count,
            },
            "reports": Barrier.reports.count(),
            "barrier_value_chart": {
                "resolved_barriers_value": resolved_barrier_value,
                "estimated_barriers_value": estimated_barrier_value,
            },
            "total_value_chart": {
                "resolved_barriers_value": total_resolved_barriers,
                "open_barriers_value": open_barriers_value,
            },
            "barriers_by_status_chart": {
                "series": status_data,
                "labels": status_labels,
            },
        }

        return Response(counts)


class BarrierReportList(BarrierReportBase, generics.ListCreateAPIView):
    # TODO - These report views may now be redundant
    serializer_class = BarrierReportSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_on",)
    ordering = ("created_on",)

    def get_queryset(self):
        """
        This view should return a list of all the reports
        for the currently authenticated user.
        """
        queryset = Barrier.reports.all()
        user = self.request.user
        return queryset.filter(created_by=user)

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        self._update_stages(serializer, self.request.user)


class BarrierReportDetail(BarrierReportBase, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "pk"
    queryset = Barrier.reports.all()
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
    queryset = Barrier.reports.all()
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
        if barrier_obj.next_steps_summary:
            kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
            Interaction(
                barrier=barrier_obj,
                text=barrier_obj.next_steps_summary,
                kind=kind,
                created_by=user,
            ).save()

        # Create default team members
        new_members = (
            TeamMember(
                barrier=barrier_obj, user=user, role=TeamMember.REPORTER, default=True
            ),
            TeamMember(
                barrier=barrier_obj, user=user, role=TeamMember.OWNER, default=True
            ),
        )
        # using a helper here due to - https://django-simple-history.readthedocs.io/en/2.8.0/common_issues.html
        bulk_create_with_history(new_members, TeamMember)


class BarrierList(generics.ListAPIView):
    """
    Return a list of all the Barriers
    with optional filtering and ordering defined
    """

    queryset = (
        Barrier.barriers.all()
        .select_related("priority")
        .prefetch_related(
            "tags", "organisations", "progress_updates", "valuation_assessments"
        )
    )
    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet

    filter_backends = (DjangoFilterBackend,)
    ordering_fields = (
        "reported_on",
        "modified_on",
        "estimated_resolution_date",
        "status",
        "priority",
        "country",
    )
    ordering = ("-reported_on",)

    def get_ordering_config(self):
        order = self.request.query_params.get("ordering", None)
        ordering_config = BARRIER_SEARCH_ORDERING_CHOICES.get(order, None)
        return ordering_config

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering_config = self.get_ordering_config()
        if ordering_config:
            order_by = ordering_config["order_on"]
            direction = ordering_config["direction"]
            ordering_filter = ordering_config.get("ordering-filter", None)

            # now we annotate the queryset with a new column - 'ordering_value' - which will contain the sort
            # order of the field we want to order on. We also use this column to implement a filter to the
            # queryset assigning 'c' value to entries(duplicates) we want to exclude from the final results
            if ordering_filter:
                # Here apply the custom logic to the extaordinary search orders e.g. barriers with multiple impact
                # assesments and sorting on resolution date
                if order_by == "valuation_assessments__impact":
                    queryset = queryset.annotate(
                        ordering_value=Case(
                            When(
                                valuation_assessments__archived=False, then=Value("a")
                            ),
                            When(valuation_assessments__archived=True, then=Value("c")),
                            default=Value("b"),
                            output_field=CharField(),
                        )
                    )
                elif order_by == "status_date":
                    queryset = queryset.annotate(
                        ordering_value=Case(
                            When(
                                status=BarrierStatus.RESOLVED_IN_FULL, then=Value("a")
                            ),
                            default=Value("b"),
                            output_field=CharField(),
                        )
                    )

                # Implement Final filter to exclude duplicates where the search option implies extra
                # filters e.g. Barriers may have multiple impact assesements
                # which could be archived therefore would result in duplicates due to annotation
                queryset = queryset.exclude(ordering_value="c")
            else:
                queryset = queryset.annotate(
                    ordering_value=Value("b", output_field=CharField())
                )

            # once we have annotated the queryset with the ordering_value, we can order by that column first, then those
            # rows which have null which be ordered by reported_on
            if direction == "ascending":
                ordered_queryset = queryset.order_by(
                    "ordering_value",
                    F(order_by).asc(nulls_last=True),
                    "-reported_on",
                )
            else:
                ordered_queryset = queryset.order_by(
                    "ordering_value",
                    F(order_by).desc(nulls_last=True),
                    "-reported_on",
                )
        else:
            ordered_queryset = queryset.order_by(
                "-reported_on",
            )

        # finally, remove duplicates from the queryset
        return ordered_queryset.distinct()

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


class BarrierRequestDownloadApproval(generics.CreateAPIView):
    """
    Handles the request for a barrier
    """

    serializer_class = BarrierRequestDownloadApprovalSerializer

    def perform_create(self, serializer):
        """
        Validates request for mandatory fields
        Creates a Barrier Instance out of the request
        """
        serializer.save(user=self.request.user)


class BarrierDetail(TeamMemberModelMixin, generics.RetrieveUpdateAPIView):
    """
    Return details of a Barrier
    Allows the barrier to be updated as well
    """

    lookup_field = "pk"
    queryset = (
        Barrier.barriers.all()
        .select_related(
            "priority",
            "created_by",
            "modified_by",
            "proposed_estimated_resolution_date_user",
        )
        .prefetch_related(
            "tags",
            Prefetch(
                "barrier_team",
                queryset=TeamMember.objects.select_related("user")
                .filter(role="Owner")
                .all(),
            ),
            "organisations",
            Prefetch(
                "progress_updates",
                queryset=BarrierProgressUpdate.objects.order_by("-created_on").all(),
            ),
            Prefetch(
                "programme_fund_progress_updates",
                queryset=ProgrammeFundProgressUpdate.objects.select_related(
                    "created_by", "modified_by"
                )
                .order_by("-created_on")
                .all(),
            ),
            "barrier_commodities",
            "public_barrier",
            "categories",
            "economic_assessments",
            "valuation_assessments",
            Prefetch(
                "next_steps_items",
                queryset=BarrierNextStepItem.objects.filter(
                    status="IN_PROGRESS"
                ).order_by("-completion_date"),
            ),
        )
    )

    serializer_class = BarrierDetailSerializer

    def get_object(self):
        if "code" in self.kwargs:
            self.lookup_url_kwarg = "code"
            self.lookup_field = "code"
        return super().get_object()

    @transaction.atomic()
    def perform_update(self, serializer):
        barrier = self.get_object()
        self.update_contributors(barrier)
        barrier = serializer.save(modified_by=self.request.user)
        self.update_metadata_for_proposed_estimated_date(barrier)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        barrier_cache.delete(pk)

    def update_metadata_for_proposed_estimated_date(self, barrier):
        # get patched data from request
        patch_data = self.request.data

        if "proposed_estimated_resolution_date" in patch_data:
            # fill date and user with requests context
            barrier.proposed_estimated_resolution_date_user = self.request.user
            barrier.proposed_estimated_resolution_date_created = datetime.now()
            barrier.save()

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        try:
            pk = self.kwargs[lookup_url_kwarg]
        except KeyError:
            """If view with `code` lookup (throws KeyError), don't cache"""
            return super().retrieve(request, *args, **kwargs)

        data = barrier_cache.get(pk)
        if data:
            return Response(data)

        response = super().retrieve(request, *args, **kwargs)

        barrier_cache.set(pk, response.data)

        return response


class BarrierFullHistory(generics.GenericAPIView):
    """
    Full audit history of changes made to a barrier and related models
    """

    def get(self, request, pk):
        barrier = Barrier.objects.get(id=self.kwargs.get("pk"))
        history_items = HistoryManager.get_full_history(
            # TODO: MAR-1068 - Re-enable use_cache=True - Temporarily disabled due to
            # not caching action plans history entries correctly
            barrier=barrier,
            ignore_creation_items=True,
        )
        response = {
            "barrier_id": str(pk),
            "history": [item.data for item in history_items],
        }
        return Response(response, status=status.HTTP_200_OK)


class BarrierActivity(generics.GenericAPIView):
    """
    Returns history items used on the barrier activity stream
    """

    def get(self, request, pk):
        barrier = Barrier.objects.get(id=self.kwargs.get("pk"))
        history_items = HistoryManager.get_activity(barrier=barrier)
        response = {
            "barrier_id": str(pk),
            "history": [item.data for item in history_items],
        }
        return Response(response, status=status.HTTP_200_OK)


class PublicBarrierActivity(generics.GenericAPIView):
    """
    Returns history items used on the public barrier activity stream
    """

    def get(self, request, pk):
        public_barrier = PublicBarrier.objects.get(barrier_id=self.kwargs.get("pk"))
        history_items = HistoryManager.get_public_activity(
            public_barrier=public_barrier
        )
        response = {
            "barrier_id": str(pk),
            "history": [item.data for item in history_items],
        }
        return Response(response, status=status.HTTP_200_OK)


class BarrierStatusBase(generics.UpdateAPIView):
    def _create(
        self,
        serializer,
        barrier_id,
        status,
        summary,
        sub_status="",
        sub_other="",
        status_date=None,
    ):
        barrier_obj = get_object_or_404(Barrier, pk=barrier_id)

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
        barrier_cache.delete(barrier_id)


class BarrierResolveInFull(BarrierStatusBase):
    queryset = Barrier.barriers.all()
    serializer_class = BarrierDetailSerializer

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
            summary=self.request.data.get("status_summary", ""),
            status_date=self.request.data.get("status_date"),
        )


class BarrierResolveInPart(BarrierStatusBase):
    queryset = Barrier.barriers.all()
    serializer_class = BarrierDetailSerializer

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
            summary=self.request.data.get("status_summary", ""),
            status_date=self.request.data.get("status_date"),
        )


class BarrierHibernate(BarrierStatusBase):
    queryset = Barrier.barriers.all()
    serializer_class = BarrierDetailSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=5,
            summary=self.request.data.get("status_summary", ""),
        )


class BarrierStatusChangeUnknown(BarrierStatusBase):
    queryset = Barrier.barriers.all()
    serializer_class = BarrierDetailSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=7,
            summary=self.request.data.get("status_summary", ""),
        )


class BarrierOpenInProgress(BarrierStatusBase):
    queryset = Barrier.barriers.all()
    serializer_class = BarrierDetailSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        self._create(
            serializer=serializer,
            barrier_id=self.kwargs.get("pk"),
            status=2,
            summary=self.request.data.get("status_summary", ""),
        )


class BarrierOpenActionRequired(BarrierStatusBase):
    queryset = Barrier.barriers.all()
    serializer_class = BarrierDetailSerializer

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
            sub_status=self.request.data.get("sub_status", ""),
            sub_other=self.request.data.get("sub_status_other", ""),
            summary=self.request.data.get("status_summary", ""),
            status_date=self.request.data.get("status_date"),
        )


class PublicBarrierViewSet(
    TeamMemberModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """
    Manage public data for barriers.
    """

    barriers_qs = (
        Barrier.barriers.all()
        .select_related("priority")
        .prefetch_related(
            "tags",
            "organisations",
        )
    )
    permission_classes = (AllRetrieveAndEditorUpdateOnly,)
    serializer_class = PublicBarrierSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = PublicBarrierFilterSet

    def get_queryset(self):
        qs = PublicBarrier.objects.filter(
            barrier__archived=False, barrier__draft=False
        ).prefetch_related(
            "notes",
            "categories",
            "barrier",
            "barrier__tags",
            "barrier__organisations",
            "barrier__categories",
            "barrier__priority",
        )

        return qs.distinct("id")

    def get_object(self) -> PublicBarrier:
        barrier = get_object_or_404(self.barriers_qs, pk=self.kwargs.get("pk"))
        public_barrier, _created = get_or_create_public_barrier(barrier)
        return public_barrier

    def update(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        self.update_contributors(public_barrier.barrier)
        return super().update(request, *args, **kwargs)

    def update_status_action(self, public_view_status):
        """
        Helper to set status of a public barrier through actions.
        :param public_view_status: Desired status
        :return: Response with serialized data
        """
        public_barrier = self.get_object()
        public_barrier.public_view_status = public_view_status
        if public_view_status is PublicBarrierStatus.ALLOWED:
            public_barrier.set_to_allowed_on = datetime.now()
        public_barrier.save()
        if public_view_status == PublicBarrierStatus.PUBLISHING_PENDING:
            TeamMember.objects.create(
                user=self.request.user,
                barrier=self.get_object().barrier,
                role=TeamMember.PUBLIC_APPROVER,
            )
        else:
            self.update_contributors(public_barrier.barrier)
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=(),
        url_path="allow-for-publishing-process",
    )
    def allow_for_publishing_process(self, request, *args, **kwargs):
        return self.update_status_action(PublicBarrierStatus.ALLOWED)

    @action(methods=["post"], detail=True, permission_classes=())
    def report_public_barrier_title(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        public_barrier.title = request.data.get("values")["title"]
        public_barrier.save()
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["post"], detail=True, permission_classes=())
    def report_public_barrier_summary(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        public_barrier.summary = request.data.get("values")["summary"]
        public_barrier.save()
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=(),
        url_path="ready-for-approval",
    )
    def ready_for_approval(self, request, *args, **kwargs):
        return self.update_status_action(PublicBarrierStatus.APPROVAL_PENDING)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=(IsApprover,),
        url_path="ready-for-publishing",
    )
    def ready_for_publishing(self, request, *args, **kwargs):
        return self.update_status_action(PublicBarrierStatus.PUBLISHING_PENDING)

    @action(methods=["post"], detail=True, permission_classes=(IsPublisher,))
    def publish(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        if (
            public_barrier.public_view_status == PublicBarrierStatus.PUBLISHING_PENDING
            or public_barrier.public_view_status == PublicBarrierStatus.UNPUBLISHED
        ):
            published = public_barrier.publish()
            TeamMember.objects.create(
                barrier=public_barrier.barrier,
                user=request.user,
                role=TeamMember.PUBLIC_PUBLISHER,
            )
        else:
            published = False
        if published:
            self.update_contributors(public_barrier.barrier)
            serializer = PublicBarrierSerializer(public_barrier)
            public_release_to_s3()
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        else:
            raise PublicBarrierPublishException()

    @action(methods=["post"], detail=True, permission_classes=(IsPublisher,))
    def unpublish(self, request, *args, **kwargs):
        r = self.update_status_action(PublicBarrierStatus.UNPUBLISHED)
        public_release_to_s3()
        return r


class BarrierProgressUpdateViewSet(ModelViewSet):
    queryset = BarrierProgressUpdate.objects.all()
    serializer_class = ProgressUpdateSerializer

    def perform_create(self, serializer, user):
        # share the exact same date within both created_on and modified_on
        now = datetime.now()
        instance = serializer.save()
        instance.created_by = user
        instance.created_on = now
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_update(self, serializer, user):
        now = datetime.now()
        instance = serializer.save()
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, request.user)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ProgrammeFundProgressUpdateViewSet(ModelViewSet):
    queryset = ProgrammeFundProgressUpdate.objects.all()
    serializer_class = ProgrammeFundProgressUpdateSerializer

    def perform_create(self, serializer, user):
        # share the exact same date within both created_on and modified_on
        now = datetime.now()
        instance = serializer.save()
        instance.created_by = user
        instance.created_on = now
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, request.user)
        headers = self.get_success_headers(serializer.data)

        barrier_cache.delete(serializer.data["barrier"])

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_update(self, serializer, user):
        now = datetime.now()
        instance = serializer.save()
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, request.user)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class BarrierPrioritySummaryViewSet(ModelViewSet):
    queryset = BarrierTopPrioritySummary.objects.all()
    serializer_class = PrioritySummarySerializer

    def get_object(self):
        return_object = BarrierTopPrioritySummary.objects.filter(
            barrier=self.kwargs.get("pk")
        )
        if return_object:
            return return_object.latest("modified_on")
        else:
            return None

    def perform_create(self, serializer, user):
        # share the exact same date within both created_on and modified_on
        now = timezone.now()
        instance = serializer.save()
        instance.created_by = user
        instance.created_on = now
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_update(self, serializer, user):
        now = timezone.now()
        instance = serializer.save()
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, request.user)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class BarrierNextStepItemViewSet(ModelViewSet):
    queryset = BarrierNextStepItem.objects.all()
    serializer_class = NextStepItemSerializer

    def get_queryset(self):
        """
        This view should return a list of all the for a barrier
        """
        barrier = self.kwargs["barrier_pk"]
        return BarrierNextStepItem.objects.filter(barrier=barrier)

    def perform_create(self, serializer, user):
        # share the exact same date within both created_on and modified_on
        now = datetime.now()
        instance = serializer.save()
        instance.created_by = user
        instance.created_on = now
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, request.user)
        headers = self.get_success_headers(serializer.data)

        barrier_cache.delete(serializer.data["barrier"])

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_update(self, serializer, user):
        now = datetime.now()
        instance = serializer.save()
        instance.modified_by = user
        instance.modified_on = now
        return instance.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, request.user)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        barrier_cache.delete(serializer.data["barrier"])

        return Response(serializer.data)
