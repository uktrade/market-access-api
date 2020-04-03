from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import BarrierInstance
from api.core.test_utils import APITestMixin, create_test_user


class TestBarrierStatusHistory(APITestMixin):
    def test_barrier_status_history_submitted(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 1,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

    def test_barrier_status_history_submitted_user(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username="Test.User"
        )

        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 1,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

    def test_barrier_status_history_submitted_resolved(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

    def test_barrier_status_history_submitted_open_and_resolved(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 1,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
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
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 1,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        history_url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
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

        open_barrier_url = reverse("open-in-progress", kwargs={"pk": instance.id})
        open_barrier_response = self.api_client.put(
            open_barrier_url, format="json", data={"status_date": "2018-09-10"}
        )
        assert open_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
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
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 1,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

        hibernate_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        hibernate_barrier_response = self.api_client.put(
            hibernate_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )
        assert hibernate_barrier_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
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
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 1,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        history_url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
        assert len(response.data["history"]) == 0

        hibernate_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        hibernate_barrier_response = self.api_client.put(
            hibernate_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )
        assert hibernate_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
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

        open_barrier_url = reverse("open-in-progress", kwargs={"pk": instance.id})
        open_barrier_response = self.api_client.put(
            open_barrier_url, format="json", data={"status_date": "2018-09-10"}
        )
        assert open_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance.id)
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
