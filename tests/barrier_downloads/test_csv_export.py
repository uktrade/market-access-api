import csv
import datetime
from io import StringIO
from unittest import skip

from django.conf import settings
from pytz import UTC
from rest_framework.test import APITestCase

from api.barrier_downloads.constants import BARRIER_FIELD_TO_COLUMN_TITLE
from api.barrier_downloads.serializers import CsvDownloadSerializer
from api.barrier_downloads.service import serializer_to_csv_bytes
from api.barriers.models import (
    Barrier,
    BarrierProgressUpdate,
    ProgrammeFundProgressUpdate,
)
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS,
    PROGRESS_UPDATE_CHOICES,
    TOP_PRIORITY_BARRIER_STATUS,
)
from api.metadata.models import Organisation
from tests.assessment.factories import EconomicImpactAssessmentFactory
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import OrganisationFactory


class TestCsvDownloadSerializer(APITestMixin, APITestCase):
    def test_summary_is_not_official_sensitive(self):
        barrier = BarrierFactory(is_summary_sensitive=False, created_by=self.mock_user)

        serializer = CsvDownloadSerializer(barrier)
        assert barrier.summary == serializer.data["summary"]

    def test_summary_is_official_sensitive(self):
        """If the summary is marked sensitive mask it in the CSV"""
        barrier = BarrierFactory(is_summary_sensitive=True)
        expected_summary = "OFFICIAL-SENSITIVE (see it on DMAS)"

        serializer = CsvDownloadSerializer(barrier)
        assert expected_summary == serializer.data["summary"]

    def test_link(self):
        """Use barrier code for the link in the CSV"""
        barrier = BarrierFactory()
        expected_link = f"{settings.DMAS_BASE_URL}/barriers/{barrier.code}"

        serializer = CsvDownloadSerializer(barrier)
        assert expected_link == serializer.data["link"]

    def test_status_date_is_null(self):
        expected_status_date = None
        barrier = BarrierFactory()
        barrier.status_date = None
        barrier.save()

        serializer = CsvDownloadSerializer(barrier)
        assert expected_status_date == serializer.data["status_date"]

    def test_resolved_date_resolved_in_full(self):
        expected_resolved_date = "17-Feb-22"
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 4
        barrier.save()

        serializer = CsvDownloadSerializer(barrier)
        assert expected_resolved_date == serializer.data["resolved_date"]

    def test_resolved_date_partially_resolved(self):
        expected_resolved_date = "17-Feb-22"
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 3
        barrier.save()

        serializer = CsvDownloadSerializer(barrier)
        assert expected_resolved_date == serializer.data["resolved_date"]

    def test_resolved_date_empty(self):
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 2
        barrier.save()

        serializer = CsvDownloadSerializer(barrier)
        assert serializer.data["resolved_date"] is None

    def test_eu_overseas_region(self):
        barrier = BarrierFactory(trading_bloc="TB00016", country=None)
        serializer = CsvDownloadSerializer(barrier)
        assert ["Europe"] == serializer.data["overseas_region"]

    def test_government_organisations(self):
        org1 = Organisation.objects.get(id=1)
        org2 = OrganisationFactory(organisation_type=0)
        barrier = BarrierFactory()
        barrier.organisations.add(org1, org2)

        assert 2 == barrier.organisations.count()
        assert 1 == barrier.government_organisations.count()

        serializer = CsvDownloadSerializer(barrier)
        assert 1 == len(serializer.data["government_organisations"])
        assert [org1.name] == serializer.data["government_organisations"]

    def test_has_value_for_is_resolved_top_priority(self):
        barrier = BarrierFactory(status_date=datetime.date.today())
        serialised_data = CsvDownloadSerializer(barrier).data
        assert "is_resolved_top_priority" in serialised_data.keys()

    def test_value_for_is_resolved_top_priority_is_bool(self):
        barrier = BarrierFactory(status_date=datetime.date.today())
        serialised_data = CsvDownloadSerializer(barrier).data
        assert isinstance(serialised_data["is_resolved_top_priority"], bool)

    def test_is_resolved_top_priority_value_for_resolved_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.RESOLVED,
        )
        serialised_data = CsvDownloadSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is True

    def test_is_resolved_top_priority_value_for_approved_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED,
        )
        serialised_data = CsvDownloadSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_approval_pending_top_priority_is_correct(
        self,
    ):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING,
        )
        serialised_data = CsvDownloadSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_removal_pending_top_priority_is_correct(
        self,
    ):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
        )
        serialised_data = CsvDownloadSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_no_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=datetime.date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.NONE,
        )
        serialised_data = CsvDownloadSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_valuation_assessment_midpoint(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        serialised_data = CsvDownloadSerializer(barrier).data

        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]
        assert "valuation_assessment_midpoint" in serialised_data.keys()
        assert (
            serialised_data["valuation_assessment_midpoint"] == expected_midpoint_value
        )

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

        serializer = CsvDownloadSerializer(barrier)
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

    def test_barrier_owner(self):
        barrier = BarrierFactory(created_by=self.mock_user)
        TeamMember.objects.create(barrier=barrier, user=self.mock_user, role="Owner")
        barrier.save()

        serializer = CsvDownloadSerializer(barrier)
        assert (
            serializer.data["barrier_owner"]
            == f"{self.mock_user.first_name} {self.mock_user.last_name}"
        )


class TestBarrierCsvExport(APITestMixin, APITestCase):
    def test_csv_has_midpoint_column(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        queryset = Barrier.objects.filter(id__in=[barrier.id])
        serializer = CsvDownloadSerializer(queryset, many=True)
        data = serializer_to_csv_bytes(serializer, BARRIER_FIELD_TO_COLUMN_TITLE)

        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]

        assert b"Midpoint value" in data
        assert expected_midpoint_value.encode("utf-8") in data

    def test_csv_has_midpoint_column_after_valuation_assessment_column(self):
        impact_level = 6
        barrier = BarrierFactory()
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        queryset = Barrier.objects.filter(id__in=[barrier.id])

        serializer = CsvDownloadSerializer(queryset, many=True)
        data = serializer_to_csv_bytes(serializer, BARRIER_FIELD_TO_COLUMN_TITLE)

        str_io = StringIO(data.decode("utf-8"))
        reader = csv.DictReader(str_io, delimiter=",")
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
        serializer = CsvDownloadSerializer(queryset, many=True)
        data = serializer_to_csv_bytes(serializer, BARRIER_FIELD_TO_COLUMN_TITLE)

        expected_midpoint_value = ""
        str_io = StringIO(data.decode("utf-8"))
        reader = csv.DictReader(str_io, delimiter=",")
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
        serialised_data = CsvDownloadSerializer(barrier).data
        assert "delivery_confidence" in serialised_data.keys()

    def test_delivery_confidence_is_on_track(self):
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        barrier: Barrier = BarrierFactory()
        barrier_progress_update_on_track = BarrierProgressUpdate.objects.create(
            barrier=barrier, status=PROGRESS_UPDATE_CHOICES.ON_TRACK, created_by=user
        )
        barrier.progress_updates.add(barrier_progress_update_on_track)
        serialised_data = CsvDownloadSerializer(barrier).data
        assert (
            "delivery_confidence" in serialised_data.keys()
            and serialised_data["delivery_confidence"]
            == PROGRESS_UPDATE_CHOICES["ON_TRACK"]
        )
