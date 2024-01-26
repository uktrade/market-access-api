from django.db.models import Count
from django.http import JsonResponse
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api.barrier_reports.tasks import generate_s3_and_send_email
from api.barriers.models import Barrier, BarrierFilterSet
from api.barriers.serializers import BarrierCsvExportSerializer
from api.user.constants import USER_ACTIVITY_EVENT_TYPES
from api.user.models import UserActvitiyLog
from api.barrier_reports.constants import BARRIER_FIELD_TO_REPORT_TITLE


class BarrierListS3EmailFile(generics.ListAPIView):
    """
    Start the following async process and return a success response

    Generate the csv file and upload it to s3.
    Generate email with link to uploaded file.
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
            "organisations",
        )
    )
    serializer_class = BarrierCsvExportSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend,)

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
        base_filename = self._get_base_filename()
        s3_filename = f"csv/{self.request.user.id}/{base_filename}.csv"
        email = self.request.user.email
        first_name = self.request.user.first_name

        queryset = self.filter_queryset(self.get_queryset()).values_list("id")

        # Create list of IDs in string format
        barrier_ids = list(map(str, queryset.values_list("id", flat=True)))

        UserActvitiyLog.objects.create(
            user=self.request.user,
            event_type=USER_ACTIVITY_EVENT_TYPES.BARRIER_CSV_DOWNLOAD,
            event_description="User has exported a CSV of barriers",
        )

        # Make celery call don't wait for return
        generate_s3_and_send_email.delay(
            barrier_ids,
            s3_filename,
            email,
            first_name,
            BARRIER_FIELD_TO_REPORT_TITLE,
        )

        return JsonResponse({"success": True})
