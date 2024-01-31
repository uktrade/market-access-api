import json
from unittest import TestCase

import mock
from rest_framework import status
from rest_framework.reverse import reverse

from api.barrier_reports.models import BarrierReport
from api.core.test_utils import APITestMixin
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
        assert response.content == b'{"error": "No barriers matching filterset"}'

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

    @mock.patch("api.barrier_reports.views.create_barrier_report")
    def test_barrier_report_post_endpoint_success_and_retrieve(
        self, mock_create_barrier_report
    ):
        barrier = BarrierFactory()
        barrier_report = BarrierReport.objects.create(user=self.user)
        mock_create_barrier_report.return_value = barrier_report
        url = reverse("barrier-reports")

        response = self.api_client.post(url)

        mock_create_barrier_report.assert_called_once_with(
            user=self.user, barrier_ids=[str(barrier.id)]
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert (
            str(barrier_report.id) == json.loads(response.content)["barrier_report_id"]
        )

        url = reverse("barrier-report", kwargs={"pk": str(barrier_report.id)})

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert json.loads(response.content)["id"] == str(barrier_report.id)

    def test_get_barrier_report(self):
        barrier_report = BarrierReport.objects.create(user=self.user)

        url = reverse("barrier-report", kwargs={"pk": str(barrier_report.id)})

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data["id"] == str(barrier_report.id)

    def test_get_barrier_report_unauthorized(self):
        # Request made as self.user
        assert self.user != self.mock_user

        barrier_report = BarrierReport.objects.create(user=self.mock_user)

        url = reverse("barrier-report", kwargs={"pk": str(barrier_report.id)})

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert data == {"detail": "Unauthorized"}

    def test_barrier_report_list(self):
        assert self.user != self.mock_user

        barrier = BarrierFactory()
        br1 = BarrierReport.objects.create(user=self.user)
        br2 = BarrierReport.objects.create(user=self.user)

        # Won't show up
        br3 = BarrierReport.objects.create(user=self.mock_user)

        url = reverse("barrier-reports")

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert len(data) == 2
        assert data[0]["id"] == str(br2.id)
        assert data[1]["id"] == str(br1.id)

    @mock.patch("api.barrier_reports.views.get_presigned_url")
    def test_get_presigned_url(self, mock_get_presigned_url):
        mock_get_presigned_url.return_value = "url.com"
        barrier_report = BarrierReport.objects.create(user=self.user)

        url = reverse(
            "get-barrier-report-presigned-url", kwargs={"pk": str(barrier_report.id)}
        )

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data == {"presigned_url": "url.com"}

    @mock.patch("api.barrier_reports.views.get_presigned_url")
    def test_get_presigned_url_unauthorized(self, mock_get_presigned_url):
        mock_get_presigned_url.return_value = "url.com"
        barrier_report = BarrierReport.objects.create(user=self.mock_user)

        url = reverse(
            "get-barrier-report-presigned-url", kwargs={"pk": str(barrier_report.id)}
        )

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert data == {"detail": "Unauthorized"}

    def test_update_report_barrier_name(self):
        barrier_report = BarrierReport.objects.create(user=self.user)

        assert barrier_report.name is None

        url = reverse("barrier-report", kwargs={"pk": str(barrier_report.id)})

        response = self.api_client.patch(url, data={"name": "New Name"})
        barrier_report.refresh_from_db()
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data["id"] == str(barrier_report.id)
        assert data["name"] == "New Name"

    def test_update_report_barrier_name_unauthorized(self):
        barrier_report = BarrierReport.objects.create(user=self.mock_user)

        assert barrier_report.name is None

        url = reverse("barrier-report", kwargs={"pk": str(barrier_report.id)})

        response = self.api_client.patch(url, data={"name": "New Name"})
        barrier_report.refresh_from_db()
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert data == {"detail": "Unauthorized"}

    def test_update_report_barrier_name_bad_request(self):
        barrier_report = BarrierReport.objects.create(user=self.user)

        assert barrier_report.name is None

        url = reverse("barrier-report", kwargs={"pk": str(barrier_report.id)})

        response = self.api_client.patch(url, data={"bad_field": "hello"})
        barrier_report.refresh_from_db()
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert data == {"name": ["This field is required."]}
