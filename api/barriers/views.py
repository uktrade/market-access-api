import csv
from collections import defaultdict
from csv import DictWriter

from dateutil.parser import parse
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, serializers, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from simple_history.utils import bulk_create_with_history

from api.barriers.csv import _transform_csv_row, create_csv_response
from api.barriers.exceptions import PublicBarrierPublishException
from api.barriers.helpers import get_or_create_public_barrier
from api.barriers.models import (
    Barrier,
    BarrierReportStage,
    PublicBarrier,
    PublicBarrierLightTouchReviews,
)
from api.barriers.serializers import (
    BarrierCsvExportSerializer,
    BarrierDetailSerializer,
    BarrierListSerializer,
    BarrierReportSerializer,
    PublicBarrierSerializer,
)
from api.collaboration.mixins import TeamMemberModelMixin
from api.collaboration.models import TeamMember
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket
from api.history.manager import HistoryManager
from api.interactions.models import Interaction
from api.metadata.constants import BARRIER_INTERACTION_TYPE, PublicBarrierStatus
from api.user.helpers import has_profile, update_user_profile
from api.user.models import (
    Profile,
    SavedSearch,
    get_my_barriers_saved_search,
    get_team_barriers_saved_search,
)
from api.user.permissions import AllRetrieveAndEditorUpdateOnly, IsEditor, IsPublisher
from api.user_event_log.constants import USER_EVENT_TYPES
from api.user_event_log.utils import record_user_event

from .models import BarrierFilterSet, PublicBarrierFilterSet
from .public_data import public_release_to_s3


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

        Profile.objects.get_or_create(user=user)
        if user.profile.sso_user_id is None:
            update_user_profile(user, self.request.auth.token)

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
            "tags",
            "organisations",
        )
    )
    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = (
        "reported_on",
        "modified_on",
        "status",
        "priority",
        "country",
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


class BarrierListExportView(generics.ListAPIView):
    """
    Superseded by BarrierListS3Download which inherits from this view.

    We now use S3 for csv downloads as it's a lot faster than streaming the file.

    Return a streaming http response of all the Barriers
    with optional filtering and ordering defined
    """

    queryset = (
        Barrier.barriers.annotate(
            team_count=Count("barrier_team"),
        )
        .all()
        .select_related(
            "wto_profile__committee_notified",
            "wto_profile__committee_raised_in",
            "priority",
            "public_barrier",
        )
        .prefetch_related(
            "economic_assessments",
            "resolvability_assessments",
            "strategic_assessments",
            "tags",
            "categories",
            "barrier_commodities",
            "public_barrier__notes",
            "cached_history_items",
            "organisations",
        )
    )
    serializer_class = BarrierCsvExportSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    field_titles = {
        "id": "id",
        "code": "code",
        "title": "Title",
        "status": "Status",
        "priority": "Priority",
        "overseas_region": "Overseas Region",
        "location": "Location",
        "admin_areas": "Admin areas",
        "sectors": "Sectors",
        "product": "Product",
        "term": "Term",
        "categories": "Barrier categories",
        "source": "Source",
        "team_count": "Team count",
        "economic_assessment_rating": "Economic assessment rating",
        "economic_assessment_explanation": "Economic assessment explanation",
        "value_to_economy": "Value to economy",
        "import_market_size": "Import market size",
        "valuation_assessment_rating": "Valuation assessment rating",
        "valuation_assessment_explanation": "Valuation assessment explanation",
        "commercial_value": "Commercial value estimate",
        "reported_on": "Reported Date",
        "status_date": "Status Date",
        "modified_on": "Last updated",
        "tags": "Tags",
        "trade_direction": "Trade direction",
        "end_date": "End date",
        "summary": "Summary",
        "link": "Link",
        "wto_has_been_notified": "WTO Notified",
        "wto_should_be_notified": "WTO Should Notify",
        "wto_committee_notified": "WTO Committee Notified",
        "wto_committee_notification_link": "WTO Committee Notified Link",
        "wto_member_states": "WTO Raised Members",
        "wto_committee_raised_in": "WTO Raised Committee",
        "wto_raised_date": "WTO Raised Date",
        "wto_case_number": "WTO Case Number",
        "commodity_codes": "HS commodity codes",
        "first_published_on": "First published date",
        "last_published_on": "Last published date",
        "public_view_status": "Public view status",
        "public_eligibility_summary": "Public eligibility summary",
        # TODO: last_public_view_status_update takes too long to calculate
        # on production, and needs to be denormalised. Will be addressed in MAR-940
        "last_public_view_status_update": "Last public view status update",
        "changed_since_published": "Changed since published",
        "public_id": "Public ID",
        "public_title": "Public title",
        "public_summary": "Public summary",
        "public_is_resolved": "Published as resolved",
        "latest_publish_note": "Latest publish note",
        "resolvability_assessment_time": "Resolvability assessment time",
        "resolvability_assessment_effort": "Resolvability assessment effort",
        "strategic_assessment_scale": "Strategic assessment scale",
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
            "Data Hub Market Access Barriers",
            now().strftime("%Y-%m-%d-%H-%M-%S"),
        ]
        return " - ".join(filename_parts)

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


class BarrierListS3Download(BarrierListExportView):
    """
    Generate the csv file and upload it to s3.

    Returns a presigned download url which is valid for an hour.
    """

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        base_filename = self._get_base_filename()

        with NamedTemporaryFile(mode="w+t") as tf:
            writer = DictWriter(
                tf,
                extrasaction="ignore",
                fieldnames=self.field_titles.keys(),
                quoting=csv.QUOTE_MINIMAL,
            )

            writer.writerow(self.field_titles)
            for row in serializer.data:
                writer.writerow(_transform_csv_row(row))
            tf.flush()

            s3_filename = f"csv/{self.request.user.id}/{base_filename}.csv"
            presigned_url = self.upload_to_s3(tf.name, s3_filename)

            return JsonResponse({"url": presigned_url})

    def upload_to_s3(self, filename, key):
        bucket_id = "default"
        bucket_name = get_bucket_name(bucket_id)
        s3_client = get_s3_client_for_bucket(bucket_id)
        s3_client.upload_file(filename, bucket_name, key)
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
        )


class BarrierDetail(TeamMemberModelMixin, generics.RetrieveUpdateAPIView):
    """
    Return details of a Barrier
    Allows the barrier to be updated as well
    """

    lookup_field = "pk"
    queryset = (
        Barrier.barriers.all()
        .select_related("priority")
        .prefetch_related(
            "barrier_commodities",
            "categories",
            "economic_assessments",
            "organisations",
            "tags",
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
        serializer.save(modified_by=self.request.user)


class BarrierFullHistory(generics.GenericAPIView):
    """
    Full audit history of changes made to a barrier and related models
    """

    def get(self, request, pk):
        barrier = Barrier.objects.get(id=self.kwargs.get("pk"))
        history_items = HistoryManager.get_full_history(
            barrier=barrier,
            ignore_creation_items=True,
            use_cache=True,
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
        history_items = HistoryManager.get_activity(barrier=barrier, use_cache=True)
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
            public_barrier=public_barrier, use_cache=False
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
    http_method_names = ["get", "post", "patch", "head", "options"]
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
            "light_touch_reviews",
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
        public_barrier.save()
        self.update_contributors(public_barrier.barrier)
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["post"], detail=True, permission_classes=(IsEditor,))
    def ready(self, request, *args, **kwargs):
        return self.update_status_action(PublicBarrierStatus.READY)

    @action(methods=["post"], detail=True, permission_classes=(IsEditor,))
    def unprepared(self, request, *args, **kwargs):
        return self.update_status_action(PublicBarrierStatus.ELIGIBLE)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=(IsEditor,),
        url_path="ignore-all-changes",
    )
    def ignore_all_changes(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        public_barrier.title = public_barrier.title
        public_barrier.summary = public_barrier.summary
        public_barrier.save()
        self.update_contributors(public_barrier.barrier)
        serializer = PublicBarrierSerializer(public_barrier)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["post"], detail=True, permission_classes=(IsPublisher,))
    def publish(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        published = public_barrier.publish()
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

    @action(methods=["post"], detail=True, permission_classes=())
    def mark_approvals(self, request, *args, **kwargs):
        public_barrier = self.get_object()
        light_touch_reviews: PublicBarrierLightTouchReviews = (
            public_barrier.light_touch_reviews
        )
        serializer = LightTouchApprovalSerializer(data=request.data.get("approvals"))
        if serializer.is_valid():
            data = serializer.validated_data

            approved_organisation_ids = []
            for organisation_approval in data["organisations"]:
                if organisation_approval["approval"]:
                    approved_organisation_ids.append(
                        organisation_approval["organisation_id"]
                    )
            light_touch_reviews.government_organisation_approvals = (
                approved_organisation_ids
            )
            light_touch_reviews.content_team_approval = data.get("content", False)
            if light_touch_reviews.content_team_approval is True:
                light_touch_reviews.has_content_changed_since_approval = False
            light_touch_reviews.hm_trade_commissioner_approval = data.get(
                "hm_commissioner", False
            )
            light_touch_reviews.save()

            return Response({"status": "success"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["post"], detail=True, permission_classes=())
    def enable_hm_trade_commissioner_approvals(self, request, *Args, **kwargs):
        public_barrier = self.get_object()
        light_touch_reviews: PublicBarrierLightTouchReviews = (
            public_barrier.light_touch_reviews
        )

        serializer = LightTouchReviewsEnableHMTradeCommissionerSerializer(
            data=request.data
        )
        if serializer.is_valid():
            data = serializer.validated_data
            light_touch_reviews.hm_trade_commissioner_approval_enabled = data["enabled"]
            light_touch_reviews.hm_trade_commissioner_approval = False
            light_touch_reviews.save()
            return Response({"status": "success"})

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LightTouchOrganisationApprovalSerializer(serializers.Serializer):
    organisation_id = serializers.CharField()
    approval = serializers.BooleanField()


class LightTouchApprovalSerializer(serializers.Serializer):
    organisations = LightTouchOrganisationApprovalSerializer(many=True)
    content = serializers.BooleanField()
    hm_commissioner = serializers.BooleanField()


class LightTouchReviewsEnableHMTradeCommissionerSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
