from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.models import BarrierInstance
from api.core.test_utils import APITestMixin, create_test_user
from tests.barriers.factories import MinReportFactory, ReportFactory


class TestBarrierStatusHistory(APITestMixin, APITestCase):

    def _submit_report(self, report):
        url = reverse("submit-report", kwargs={"pk": report.id})
        return self.api_client.put(url, format="json", data={})

    def setUp(self):
        self.report = ReportFactory()
        self.url = reverse("status-history", kwargs={"pk": self.report.id})

    def test_barrier_status_history_submitted(self):
        self._submit_report(self.report)
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 0

    def test_barrier_status_history_submitted_resolved(self):
        self._submit_report(self.report)
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 0

    def test_barrier_status_history_submitted_open_and_resolved(self):
        self._submit_report(self.report)
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 0

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": self.report.id})
        self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 1
        assert response.data["history"][0]["old_value"] == "1"
        assert response.data["history"][0]["new_value"] == "4"
        assert (
            response.data["history"][0]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert (
            response.data["history"][0]["field_info"]["status_summary"]
            == "dummy summary"
        )

    def test_barrier_status_history_submitted_open_and_resolved_and_open(self):
        self._submit_report(self.report)
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 0

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": self.report.id})
        self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 1
        assert response.data["history"][0]["old_value"] == "1"
        assert response.data["history"][0]["new_value"] == "4"
        assert (
            response.data["history"][0]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert (
            response.data["history"][0]["field_info"]["status_summary"]
            == "dummy summary"
        )

        open_barrier_url = reverse("open-in-progress", kwargs={"pk": self.report.id})
        open_barrier_response = self.api_client.put(
            open_barrier_url, format="json", data={"status_date": "2018-09-10"}
        )
        assert open_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 2
        assert response.data["history"][0]["old_value"] == "1"
        assert response.data["history"][0]["new_value"] == "4"
        assert (
            response.data["history"][0]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert (
            response.data["history"][0]["field_info"]["status_summary"]
            == "dummy summary"
        )
        assert response.data["history"][1]["old_value"] == "4"
        assert response.data["history"][1]["new_value"] == "2"
        assert (
            response.data["history"][1]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert response.data["history"][1]["field_info"]["status_summary"] is None

    def test_barrier_status_history_submitted_open_and_hibernated(self):
        self._submit_report(self.report)
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 0

        hibernate_barrier_url = reverse("hibernate-barrier", kwargs={"pk": self.report.id})
        hibernate_barrier_response = self.api_client.put(
            hibernate_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )
        assert hibernate_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 1
        assert response.data["history"][0]["old_value"] == "1"
        assert response.data["history"][0]["new_value"] == "5"
        assert (
            response.data["history"][0]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert (
            response.data["history"][0]["field_info"]["status_summary"]
            == "dummy summary"
        )

    def test_barrier_status_history_submitted_open_and_hibernated_and_open(self):
        self._submit_report(self.report)
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 0

        hibernate_barrier_url = reverse("hibernate-barrier", kwargs={"pk": self.report.id})
        hibernate_barrier_response = self.api_client.put(
            hibernate_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )
        assert hibernate_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 1
        assert response.data["history"][0]["old_value"] == "1"
        assert response.data["history"][0]["new_value"] == "5"
        assert (
            response.data["history"][0]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert (
            response.data["history"][0]["field_info"]["status_summary"]
            == "dummy summary"
        )

        open_barrier_url = reverse("open-in-progress", kwargs={"pk": self.report.id})
        open_barrier_response = self.api_client.put(
            open_barrier_url, format="json", data={"status_date": "2018-09-10"}
        )
        assert open_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(self.report.id)
        assert len(response.data["history"]) == 2
        assert response.data["history"][0]["old_value"] == "1"
        assert response.data["history"][0]["new_value"] == "5"
        assert (
            response.data["history"][0]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert (
            response.data["history"][0]["field_info"]["status_summary"]
            == "dummy summary"
        )
        assert response.data["history"][1]["old_value"] == "5"
        assert response.data["history"][1]["new_value"] == "2"
        assert (
            response.data["history"][1]["field_info"]["event"]
            == "BARRIER_STATUS_CHANGE"
        )
        assert response.data["history"][1]["field_info"]["status_summary"] is None
