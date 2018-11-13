from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import BarrierInstance
from api.core.test_utils import APITestMixin, create_test_user


class TestBarrierDetail(APITestMixin):
    def test_barriers_with_sso_kind_user(self):
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

        url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # assert response["reported_by"] == self.user.username


    def test_barrier_with_user_empty_username(self):
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

    def test_barrier_with_user_email_as_username(self):
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

    def test_barrier_with_user_normal_username(self):
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

    def test_barrier_with_user_normal_username_and_email(self):
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

    def test_barrier_status_history_submitted(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][0]["status_date"] is not None
        assert response.data["status_history"][0]["date"] is not None
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][0]["status_date"] is not None
        assert response.data["status_history"][0]["date"] is not None

    def test_barrier_status_history_submitted_user(self):
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][0]["user"]["name"] == "Test.User"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][1]["user"]["name"] == "Test.User"
    def test_barrier_status_history_submitted_resolved(self):
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

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 4
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"

    def test_barrier_status_history_submitted_open_and_resolved(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"

        resolve_barrier_url = reverse("resolve-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(resolve_barrier_url, format="json", data={
            "status": 4,
            "status_date": "2018-09-10",
            "status_summary": "dummy summary"
        })

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 3
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][2]["old_status"] == 2
        assert response.data["status_history"][2]["new_status"] == 4
        assert response.data["status_history"][2]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][2]["status_summary"] == "dummy summary"

    def test_barrier_status_history_submitted_open_and_resolved_and_open(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        history_url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"

        resolve_barrier_url = reverse("resolve-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(resolve_barrier_url, format="json", data={
            "status": 4,
            "status_date": "2018-09-10",
            "status_summary": "dummy summary"
        })

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 3
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][2]["old_status"] == 2
        assert response.data["status_history"][2]["new_status"] == 4
        assert response.data["status_history"][2]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][2]["status_summary"] == "dummy summary"

        open_barrier_url = reverse("open-barrier", kwargs={"pk": instance.id})
        open_barrier_response = self.api_client.put(open_barrier_url, format="json", data={
            "status": 2,
            "status_date": "2018-09-10",
        })
        assert open_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 4
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][2]["old_status"] == 2
        assert response.data["status_history"][2]["new_status"] == 4
        assert response.data["status_history"][2]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][2]["status_summary"] == "dummy summary"
        assert response.data["status_history"][3]["old_status"] == 4
        assert response.data["status_history"][3]["new_status"] == 2
        assert response.data["status_history"][3]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][3]["status_summary"] is None

    def test_barrier_status_history_submitted_open_and_hibernated(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"

        hibernate_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        hibernate_barrier_response = self.api_client.put(hibernate_barrier_url, format="json", data={
            "status": 5,
            "status_date": "2018-09-10",
            "status_summary": "dummy summary"
        })
        assert hibernate_barrier_response.status_code == status.HTTP_200_OK

        url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 3
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][2]["old_status"] == 2
        assert response.data["status_history"][2]["new_status"] == 5
        assert response.data["status_history"][2]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][2]["status_summary"] == "dummy summary"

    def test_barrier_status_history_submitted_open_and_hibernated_and_open(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        history_url = reverse("status-history", kwargs={"pk": instance.id})
        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 2
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"

        hibernate_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        hibernate_barrier_response = self.api_client.put(hibernate_barrier_url, format="json", data={
            "status": 5,
            "status_date": "2018-09-10",
            "status_summary": "dummy summary"
        })
        assert hibernate_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 3
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][2]["old_status"] == 2
        assert response.data["status_history"][2]["new_status"] == 5
        assert response.data["status_history"][2]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][2]["status_summary"] == "dummy summary"

        open_barrier_url = reverse("open-barrier", kwargs={"pk": instance.id})
        open_barrier_response = self.api_client.put(open_barrier_url, format="json", data={
            "status": 2,
            "status_date": "2018-09-10",
        })
        assert open_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(history_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == instance.id
        assert len(response.data["status_history"]) == 4
        assert response.data["status_history"][0]["old_status"] is None
        assert response.data["status_history"][0]["new_status"] == 0
        assert response.data["status_history"][0]["event"] == "REPORT_CREATED"
        assert response.data["status_history"][1]["old_status"] == 0
        assert response.data["status_history"][1]["new_status"] == 2
        assert response.data["status_history"][1]["event"] == "BARRIER_CREATED"
        assert response.data["status_history"][2]["old_status"] == 2
        assert response.data["status_history"][2]["new_status"] == 5
        assert response.data["status_history"][2]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][2]["status_summary"] == "dummy summary"
        assert response.data["status_history"][3]["old_status"] == 5
        assert response.data["status_history"][3]["new_status"] == 2
        assert response.data["status_history"][3]["event"] == "BARRIER_STATUS_CHANGE"
        assert response.data["status_history"][3]["status_summary"] is None
