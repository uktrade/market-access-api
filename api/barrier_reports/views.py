from django.db.models import Count
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api.barriers.models import Barrier, BarrierFilterSet
from api.barriers.serializers import BarrierCsvExportSerializer
from api.user.constants import USER_ACTIVITY_EVENT_TYPES
from api.user.models import UserActvitiyLog
from django.utils.timezone import now
from api.barrier_reports.tasks import generate_s3_and_send_email

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

    field_titles = {
        "id": "id",
        "code": "code",
        "title": "Title",
        "status": "Status",
        "priority": "Old Priority",
        "priority_level": "Priority",
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
        "valuation_assessment_midpoint": "Midpoint value",
        "valuation_assessment_explanation": "Valuation assessment explanation",
        "commercial_value": "Commercial value estimate",
        "reported_on": "Reported Date",
        "status_date": "Status effective from date",
        "resolved_date": "Resolved Date",
        "status_summary": "Status summary",
        "modified_on": "Last updated",
        "tags": "Tags",
        "trade_direction": "Trade direction",
        "estimated_resolution_date": "Estimated resolution date",
        "proposed_estimated_resolution_date": "Proposed estimated resolution date",
        "previous_estimated_resolution_date": "The previous estimate for resolution date",
        "estimated_resolution_updated_date": "The last date the resolution date was re-estimated",
        "estimated_resolution_date_change_reason": "The reason for change to the estimated resolution date",
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
        "is_top_priority": "Is Top Priority",
        "top_priority_status": "Top Priority Status",
        "top_priority_summary": "Reason for Top Priority Status",
        "is_resolved_top_priority": "Is Resolved Top Priority",
        "government_organisations": "Related Organisations",
        "progress_update_status": "Progress update status",
        "progress_update_message": "Progress update message",
        "progress_update_date": "Progress update date",
        "progress_update_author": "Progress update author",
        "progress_update_next_steps": "Progress update next steps",
        "next_steps_items": "Progress update list of next steps",
        "programme_fund_progress_update_milestones": "Programme fund milestones",
        "programme_fund_progress_update_expenditure": "Programme fund expenditure",
        "programme_fund_progress_update_date": "Programme fund date",
        "programme_fund_progress_update_author": "Programme fund author",
    }

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
            self.field_titles,
        )

        return JsonResponse({"success": True})
