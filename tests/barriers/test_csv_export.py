import datetime
from unittest import skip

from django.conf import settings
from rest_framework.test import APITestCase

from api.barriers.models import Barrier, BarrierProgressUpdate
from api.barriers.serializers import BarrierCsvExportSerializer
from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.constants import PROGRESS_UPDATE_CHOICES
from api.metadata.models import Organisation
from tests.assessment.factories import EconomicAssessmentFactory
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import BarrierTagFactory, OrganisationFactory


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

    def test_resolved_date(self):
        expected_resolved_date = "02/2022"
        barrier = BarrierFactory()
        barrier.status_date = datetime.datetime(2022, 2, 17)
        barrier.status = 4
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_resolved_date == serializer.data["resolved_date"]

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
        tag_title = "Very Important Thing"
        tag = BarrierTagFactory(title=tag_title, is_top_priority_tag=True)
        barrier = BarrierFactory(tags=(tag,), status_date=datetime.date.today())
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert (
            "is_top_priority" in serialised_data.keys()
            and serialised_data["is_top_priority"] is True
        )

    def test_is_not_top_priority_barrier(self):
        tag_title = "Very Important Thing"
        tag = BarrierTagFactory(title=tag_title, is_top_priority_tag=False)
        barrier = BarrierFactory(tags=(tag,), status_date=datetime.date.today())
        serialised_data = BarrierCsvExportSerializer(barrier).data
        assert (
            "is_top_priority" in serialised_data.keys()
            and serialised_data["is_top_priority"] is False
        )


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
