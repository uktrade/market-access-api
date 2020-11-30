from django.conf import settings

from rest_framework.test import APITestCase

from api.barriers.serializers import BarrierCsvExportSerializer
from api.core.test_utils import APITestMixin
from api.metadata.models import Organisation

from tests.assessment.factories import EconomicAssessmentFactory
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import OrganisationFactory


class TestBarrierCsvExportSerializer(APITestMixin, APITestCase):

    def test_summary_is_not_official_sensitive(self):
        barrier = BarrierFactory(is_summary_sensitive=False)

        serializer = BarrierCsvExportSerializer(barrier)
        assert barrier.summary == serializer.data["summary"]

    def test_summary_is_official_sensitive(self):
        """ If the summary is marked sensitive mask it in the CSV """
        barrier = BarrierFactory(is_summary_sensitive=True)
        expected_summary = "OFFICIAL-SENSITIVE (see it on DMAS)"

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_summary == serializer.data["summary"]

    def test_link(self):
        """ Use barrier code for the link in the CSV """
        barrier = BarrierFactory()
        expected_link = f"{settings.DMAS_BASE_URL}/barriers/{barrier.code}"

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_link == serializer.data["link"]

    def test_economic_assessment(self):
        """ Include Assessment Explanation in the CSV """
        expected_explanation = "Wibble wobble!"
        barrier = BarrierFactory()
        EconomicAssessmentFactory(barrier=barrier, approved=True, explanation=expected_explanation)

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_explanation == serializer.data["economic_assessment_explanation"]

    def test_ecomomic_assessment_is_none(self):
        """ Default to None if there's no Assessment for the Barrier """
        expected_explanation = None
        barrier = BarrierFactory()

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_explanation == serializer.data["economic_assessment_explanation"]

    def test_status_date_is_null(self):
        expected_status_date = None
        barrier = BarrierFactory()
        barrier.status_date = None
        barrier.save()

        serializer = BarrierCsvExportSerializer(barrier)
        assert expected_status_date == serializer.data["status_date"]

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
