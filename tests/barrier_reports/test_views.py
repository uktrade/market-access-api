import json
from unittest import TestCase

from django.http import JsonResponse
from rest_framework import status
from rest_framework.reverse import reverse
from freezegun import freeze_time
import mock
from api.core.test_utils import APITestMixin
from api.barrier_reports.models import BarrierReport
from tests.barriers.factories import BarrierFactory


class TestBarrierReportViews(APITestMixin, TestCase):
    fixtures = ["users"]

    def setUp(self):
        super().setUp()

    def test_barrier_report_post_endpoint_no_results(self):
        url = reverse("barrier-reports")

        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content == b'{"error": "No barriers matching filterset"}'

    def test_barrier_report_post_endpoint_no_results_filter(self):
        barrier = BarrierFactory()
        url = f'{reverse("barrier-reports")}?text=wrong-{barrier.title}'

        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content ==b'{"error": "No barriers matching filterset"}'

    def test_barrier_report_post_endpoint_success(self):
        barrier = BarrierFactory()
        url = reverse("barrier-reports")

        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED

    def test_barrier_report_post_endpoint_success_with_filter(self):
        barrier = BarrierFactory()
        url = f'{reverse("barrier-reports")}?text={barrier.title}'

        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED

    # @mock.patch('api.barrier_reports.service')
    # def test_barrier_report_post_endpoint_success_and_retrieve(self, mock_service):
    #     barrier = BarrierFactory()
    #     barrier_report = BarrierReport.objects.create()
    #     mock_service.create_barrier_report.return_value = barrier_report
    #     url = reverse("barrier-reports")
    #
    #     response = self.api_client.post(url)
    #
    #     assert response.status_code == status.HTTP_201_CREATED
    #     assert str(barrier_report.id) == json.loads(response.content)['barrier_report_id']
    #
    #     url = reverse("get-barrier-report", kwargs={'pk': str(barrier_report.id)})
    #
    #     response = self.api_client.get(url)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert response.content == ''
