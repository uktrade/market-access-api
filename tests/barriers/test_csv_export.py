from rest_framework.test import APITestCase

from barriers.serializers import BarrierCsvExportSerializer
from core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory


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
