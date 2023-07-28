import csv
import datetime
from io import StringIO
from unittest import skip

from django.conf import settings
from mock.mock import mock_open, patch
from pytz import UTC
from rest_framework.test import APITestCase

from api.barriers.models import (
    Barrier,
    BarrierProgressUpdate,
    BarrierTopPrioritySummary,
    ProgrammeFundProgressUpdate,
)
from api.barriers.serializers import BarrierCsvExportSerializer
from api.barriers.tasks import create_named_temporary_file, write_to_temporary_file
from api.barriers.views import BarrierListS3EmailFile
from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS,
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC,
    PROGRESS_UPDATE_CHOICES,
    TOP_PRIORITY_BARRIER_STATUS,
)
from api.metadata.models import ExportType, Organisation
from tests.assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
)
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import OrganisationFactory


class TestBarrierCsvExportSerializer(APITestMixin, APITestCase):
    def test_summary_is_not_official_sensitive(self):
        barrier = BarrierFactory(is_summary_sensitive=False)

        serializer = BarrierCsvExportSerializer(barrier)
        assert barrier.summary == serializer.data["summary"]

    def test_summary_is_official_sensitive(self):
        """If the summary is marked sensitive mask it in the CSV"""
        barrier = BarrierFactory(is_summary_sensitive=True)
        expected_summary = "OFFICIAL-SENSITIVE (see it on DMAS)"

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_summary == serializer.data["summary"]

    def test_link(self):
        """Use barrier code for the link in the CSV"""
        barrier = BarrierFactory()
        expected_link = f"{settings.DMAS_BASE_URL}/barriers/{barrier.code}"

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_link == serializer.data["link"]

    def test_economic_assessment(self):
        """Include Assessment Explanation in the CSV"""
        expected_explanation = "Wibble wobble!"
        barrier = BarrierFactory()
        EconomicAssessmentFactory(
            barrier=barrier, approved=True, explanation=expected_explanation
        )

        serializer = BarrierCsvExportSerializer(barrier)
        assert (
            expected_explanation == serializer.data["economic_assessment_explanation"]
        )

    def test_ecomomic_assessment_is_none(self):
        """Default to None if there's no Assessment for the Barrier"""
        expected_explanation = None
        barrier = BarrierFactory()

        serializer = BarrierCsvExportSerializer(barrier)
        assert (
            expected_explanation == serializer.data["economic_assessment_explanation"]
        )

    def test_status_date_is_null(self):
        expected_status_date = None
        barrier = BarrierFactory()
        barrier.status_date = None
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_status_date == serializer.data["status_date"]

    def test_resolved_date_resolved_in_full(self):
        expected_resolved_date = "17-Feb-22"
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 4
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_resolved_date == serializer.data["resolved_date"]

    def test_resolved_date_partially_resolved(self):
        expected_resolved_date = "17-Feb-22"
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 3
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_resolved_date == serializer.data["resolved_date"]

    def test_resolved_date_empty(self):
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 2
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["resolved_date"] is None

    def test_eu_overseas_region(self):
        barrier = BarrierFactory(trading_bloc="TB00016", country=None)
        serializer = BarrierCsvExportSerializer(barrier)
        assert ["Europe"] == serializer.data["overseas_region"]

    def test_government_organisations(self):
        org1 = Organisation.objects.get(id=1)
        org2 = OrganisationFactory(organisation_type=0)
        barrier = BarrierFactory()
        barrier.organisations.add(org1, org2)

        assert 2 == barrier.organisations.count()
        assert 1 == barrier.government_organisations.count()

        serializer = BarrierCsvExportSerializer(barrier)
        assert 1 == len(serializer.data["government_organisations"])
        assert [org1.name] == serializer.data["government_organisations"]

    def test_has_value_for_is_top_priority(self):
        barrier = BarrierFactory()
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert "is_top_priority" in serialised_data.keys()

    def test_value_for_is_top_priority_is_bool(self):
        barrier = BarrierFactory()
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert "is_top_priority" in serialised_data.keys() and isinstance(
            serialised_data["is_top_priority"], bool
        )

    def test_is_top_priority_barrier(self):

        # Left: top_priority_status - Right: expected is_top_priority value
        top_priority_status_to_is_top_priority_map = {
            TOP_PRIORITY_BARRIER_STATUS.APPROVED: True,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING: True,
            TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING: False,
            TOP_PRIORITY_BARRIER_STATUS.NONE: False,
            TOP_PRIORITY_BARRIER_STATUS.RESOLVED: False,
        }

        for (
            top_priority_status,
            is_top_priority,
        ) in top_priority_status_to_is_top_priority_map.items():
            barrier = BarrierFactory(
                top_priority_status=top_priority_status,
                status_date=datetime.date.today(),
            )
            serialised_data = BarrierCsvExportSerializer(barrier).data
            assert serialised_data["top_priority_status"] == top_priority_status
            assert is_top_priority == serialised_data["is_top_priority"]

    def test_top_priority_status(self):
        top_priority_summary = "PB100 status summary"
        top_priority_status_to_is_top_priority_map = {
            TOP_PRIORITY_BARRIER_STATUS.APPROVED: True,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING: True,
            TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING: False,
            TOP_PRIORITY_BARRIER_STATUS.NONE: False,
            TOP_PRIORITY_BARRIER_STATUS.RESOLVED: False,
        }
        for (
            top_priority_status,
            is_top_priority,
        ) in top_priority_status_to_is_top_priority_map.items():
            expected_top_priority_summary = (
                top_priority_summary if is_top_priority else ""
            )
            barrier = BarrierFactory(
                top_priority_status=top_priority_status,
                status_date=datetime.date.today(),
            )
            summary = BarrierTopPrioritySummary()
            summary.barrier = barrier
            summary.top_priority_summary_text = expected_top_priority_summary
            summary.save()
            serialised_data = BarrierCsvExportSerializer(barrier).data
            assert serialised_data["top_priority_status"] == top_priority_status
            assert "top_priority_summary" in serialised_data
            assert (
                serialised_data["top_priority_summary"] == expected_top_priority_summary
            )

    def test_has_value_for_is_resolved_top_priority(self):
        barrier = BarrierFactory(status_date=datetime.date.today())
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert "is_resolved_top_priority" in serialised_data.keys()

    def test_value_for_is_resolved_top_priority_is_bool(self):
        barrier = BarrierFactory(status_date=datetime.date.today())
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert isinstance(serialised_data["is_resolved_top_priority"], bool)

    def test_is_resolved_top_priority_value_for_resolved_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.RESOLVED,
        )
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is True

    def test_is_resolved_top_priority_value_for_approved_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED,
        )
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_approval_pending_top_priority_is_correct(
        self,
    ):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING,
        )
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_removal_pending_top_priority_is_correct(
        self,
    ):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
        )
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_no_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.NONE,
        )
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_valuation_assessment_midpoint(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        serialised_data = BarrierCsvExportSerializer(barrier).data

        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]
        assert "valuation_assessment_midpoint" in serialised_data.keys()
        assert (
            serialised_data["valuation_assessment_midpoint"] == expected_midpoint_value
        )

    def test_valuation_assessment_midpoint_value(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        serialised_data = BarrierCsvExportSerializer(barrier).data

        expected_midpoint = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]
        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC[
            expected_midpoint
        ]
        assert "valuation_assessment_midpoint_value" in serialised_data.keys()
        assert (
            serialised_data["valuation_assessment_midpoint_value"]
            == expected_midpoint_value
        )

    def test_previous_estimated_resolution_date(self):
        barrier = BarrierFactory(estimated_resolution_date="2022-10-01")
        barrier.estimated_resolution_date = "2022-12-01"
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["previous_estimated_resolution_date"] == "Oct-22"
        assert serializer.data[
            "estimated_resolution_updated_date"
        ] == datetime.date.today().strftime("%Y-%m-%d")

    def test_previous_estimated_resolution_date_empty(self):
        barrier = BarrierFactory()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["previous_estimated_resolution_date"] is None
        assert serializer.data["estimated_resolution_updated_date"] is None

    def test_programme_fund_progress_update_fields_present(self):
        barrier = BarrierFactory()
        data = {
            "barrier": barrier,
            "milestones_and_deliverables": "Test milestones and deliverables",
            "expenditure": "Test expenditure",
            "created_on": datetime.datetime.now(tz=UTC),
            "created_by": self.user,
        }
        programme_fund_update = ProgrammeFundProgressUpdate.objects.create(**data)

        serializer = BarrierCsvExportSerializer(barrier)
        assert (
            serializer.data["programme_fund_progress_update_milestones"]
            == data["milestones_and_deliverables"]
        )
        assert (
            serializer.data["programme_fund_progress_update_expenditure"]
            == data["expenditure"]
        )
        assert (
            serializer.data["programme_fund_progress_update_date"] == data["created_on"]
        )
        assert (
            serializer.data["programme_fund_progress_update_author"]
            == f"{self.user.first_name} {self.user.last_name}"
        )

    def test_start_date(self):
        barrier = BarrierFactory(start_date="2022-10-01")

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["start_date"] == "Oct-22"

    def test_main_sector(self):
        barrier = BarrierFactory()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["main_sector"] is not None

    def test_export_types(self):
        barrier = BarrierFactory()
        export_type = ExportType.objects.first()
        barrier.export_types.add(export_type)
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["export_types"] == [export_type.name]

    def test_is_currently_active(self):
        barrier = BarrierFactory()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["is_currently_active"] is True

    def test_export_description(self):
        barrier = BarrierFactory()
        barrier.export_description = "Export summary\nExport description"
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["export_description"] == [
            "Export summary",
            "Export description",
        ]

    def test_all_sectors(self):
        barrier = BarrierFactory()
        barrier.all_sectors = True
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert serializer.data["all_sectors"] is True


class TestBarrierCsvExport(APITestMixin, APITestCase):
    def get_content_written_to_csv(self, queryset):
        field_titles = BarrierListS3EmailFile.field_titles
        serializer = BarrierCsvExportSerializer(queryset, many=True)
        mocked_open = mock_open()
        with patch("api.barriers.tasks.NamedTemporaryFile", mocked_open):
            with create_named_temporary_file() as temporary_file:
                write_to_temporary_file(temporary_file, field_titles, serializer)
        mock_handle = mocked_open()
        written = "".join([str(call.args[0]) for call in mock_handle.write.mock_calls])
        return written

    def test_csv_output_uses_encoding_that_works_with_excel(self):
        mocked_open = mock_open()
        with patch("api.barriers.tasks.NamedTemporaryFile", mocked_open):
            with create_named_temporary_file():
                pass

        mocked_open.assert_called_with(mode="w+t", encoding="utf-8-sig")

    def test_csv_has_midpoint_column(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        queryset = Barrier.objects.filter(id__in=[barrier.id])

        written = self.get_content_written_to_csv(queryset)

        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]
        io = StringIO(written)
        reader = csv.DictReader(io, delimiter=",")
        for row in reader:
            break
        assert "Midpoint value" in row.keys()
        assert row["Midpoint value"] == expected_midpoint_value

    def test_csv_has_midpoint_column_after_valuation_assessment_column(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        queryset = Barrier.objects.filter(id__in=[barrier.id])

        written = self.get_content_written_to_csv(queryset)

        io = StringIO(written)
        reader = csv.DictReader(io, delimiter=",")
        for row in reader:
            break
        # indexing the result of a dict's keys() method isn't supported in Python 3
        keys_list = list(row.keys())
        index_of_midpoint_value_column = keys_list.index("Midpoint value")
        preceding_column_key = keys_list[index_of_midpoint_value_column - 1]
        assert preceding_column_key == "Valuation assessment rating"

    def test_csv_midpoint_column_is_empty_string_for_no_valuation_assessment(self):
        barrier = BarrierFactory()
        queryset = Barrier.objects.filter(id__in=[barrier.id])

        written = self.get_content_written_to_csv(queryset)

        expected_midpoint_value = ""
        io = StringIO(written)
        reader = csv.DictReader(io, delimiter=",")
        for row in reader:
            break
        assert "Midpoint value" in row.keys()
        assert row["Midpoint value"] == expected_midpoint_value


@skip(
    "These will come in handy should they decide they want the 'Delivery Confidence' column to contain some data"
)
class TestBarrierCsvExportDeliveryConfidenceSerializer(APITestMixin, APITestCase):
    def test_delivery_confidence_in_response(self):
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        barrier: Barrier = BarrierFactory()
        barrier_progress_update_on_track = BarrierProgressUpdate.objects.create(
            barrier=barrier, status=PROGRESS_UPDATE_CHOICES.ON_TRACK, created_by=user
        )
        barrier.progress_updates.add(barrier_progress_update_on_track)
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert "delivery_confidence" in serialised_data.keys()

    def test_delivery_confidence_is_on_track(self):
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        barrier: Barrier = BarrierFactory()
        barrier_progress_update_on_track = BarrierProgressUpdate.objects.create(
            barrier=barrier, status=PROGRESS_UPDATE_CHOICES.ON_TRACK, created_by=user
        )
        barrier.progress_updates.add(barrier_progress_update_on_track)
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert (
            "delivery_confidence" in serialised_data.keys()
            and serialised_data["delivery_confidence"]
            == PROGRESS_UPDATE_CHOICES["ON_TRACK"]
        )
