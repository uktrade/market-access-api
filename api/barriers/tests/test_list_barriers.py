from rest_framework import status
from rest_framework.reverse import reverse

from django.utils.timezone import now

from api.core.test_utils import APITestMixin, create_test_user
from ..models import BarrierInstance
from .test_utils import TestUtils


class TestListBarriers(APITestMixin):
    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_no_reports_counts(self):
        """Test there are no reports using list"""
        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 0
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["resolved"] == 0
        assert response.data["reports"] == 0
        assert response.data["user"]["barriers"] == 0
        assert response.data["user"]["reports"] == 0

    def test_list_barriers_report_is_not_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_report_is_not_barrier_counts(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 0
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["resolved"] == 0
        assert response.data["reports"] == 1
        assert response.data["user"]["barriers"] == 0
        assert response.data["user"]["reports"] == 1

    def test_list_barriers_get_one_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_barriers_get_one_barrier_counts(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 1
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["resolved"] == 1
        assert response.data["reports"] == 0
        assert response.data["user"]["barriers"] == 1
        assert response.data["user"]["reports"] == 0

    def test_list_barriers_get_multiple_barriers(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 1,
            "is_resolved": False,
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_barriers_get_multiple_barriers_country_filter(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 1,
            "is_resolved": False,
            "export_country": "af959812-6095-e211-a939-e4115bead28a",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"export_country": "af959812-6095-e211-a939-e4115bead28a"})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_barriers_get_multiple_barriers_country_filter_all(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "af959812-6095-e211-a939-e4115bead28a",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 1,
            "is_resolved": False,
            "export_country": "af959812-6095-e211-a939-e4115bead28a",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"export_country": "af959812-6095-e211-a939-e4115bead28a"})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
    def test_list_barriers_get_multiple_barriers_country_filter_no_results(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 1,
            "is_resolved": False,
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"export_country": "af959812-6095-e211-a939-e4115bead28a"})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
