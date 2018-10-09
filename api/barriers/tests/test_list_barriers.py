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
        assert response.data["barrier_count"] == 0
        assert response.data["unfinished_report_count"] == 0
        assert response.data["user"]["barrier_count"] == 0
        assert response.data["user"]["unfinished_report_count"] == 0

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
        assert response.data["barrier_count"] == 0
        assert response.data["unfinished_report_count"] == 1
        assert response.data["user"]["barrier_count"] == 0
        assert response.data["user"]["unfinished_report_count"] == 1

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
        assert response.data["barrier_count"] == 1
        assert response.data["unfinished_report_count"] == 0
        assert response.data["user"]["barrier_count"] == 1
        assert response.data["user"]["unfinished_report_count"] == 0

    def test_list_barriers_get_one_barrier_with_sso_kind_user(self):
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
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == self.user.username


    def test_list_barriers_get_one_barrier_with_user_empty_username(self):
        a_user = create_test_user(
            first_name="",
            last_name="",
            email="Testo@Useri.com",
            username="",
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(list_report_url, format="json", data={
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Testo"

    def test_list_barriers_get_one_barrier_with_user_email_as_username(self):
        a_user = create_test_user(
            first_name="",
            last_name="",
            email="",
            username="Testo@Useri.com",
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(list_report_url, format="json", data={
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Testo"

    def test_list_barriers_get_one_barrier_with_user_normal_username(self):
        a_user = create_test_user(
            first_name="",
            last_name="",
            email="",
            username="Test.User",
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(list_report_url, format="json", data={
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Test.User"

    def test_list_barriers_get_one_barrier_with_user_normal_username_and_email(self):
        a_user = create_test_user(
            first_name="",
            last_name="",
            email="Testo@Useri.com",
            username="Test.User",
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(list_report_url, format="json", data={
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Test.User"

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

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"country": "af959812-6095-e211-a939-e4115bead28a"})

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

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"country": "af959812-6095-e211-a939-e4115bead28a"})

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

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"country": "af959812-6095-e211-a939-e4115bead28a"})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
