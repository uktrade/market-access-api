from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import BarrierInstance
from api.metadata.models import BarrierType
from api.core.test_utils import APITestMixin, create_test_user


class TestBarrierDetail(APITestMixin):
    def test_barriers_with_sso_kind_user(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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

        url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # assert response["reported_by"] == self.user.username

    def test_barrier_with_user_empty_username(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username=""
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = new_api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        barrier = response.data
        assert barrier["reported_by"] == "Testo"
        assert barrier["created_on"] is not None
        assert barrier["modified_by"] == "Testo"
        assert barrier["modified_by"] is not None

    def test_barrier_with_user_email_as_username(self):
        a_user = create_test_user(
            first_name="", last_name="", email="", username="Testo@Useri.com"
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = new_api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        barrier = response.data
        assert barrier["reported_by"] == "Testo"
        assert barrier["created_on"] is not None
        assert barrier["modified_by"] == "Testo"
        assert barrier["modified_by"] is not None

    def test_barrier_with_user_normal_username(self):
        a_user = create_test_user(
            first_name="", last_name="", email="", username="Test.User"
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = new_api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        barrier = response.data
        assert barrier["reported_by"] == "Test.User"
        assert barrier["created_on"] is not None
        assert barrier["modified_by"] == "Test.User"
        assert barrier["modified_by"] is not None

    def test_barrier_with_user_normal_username_and_email(self):
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
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = new_api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        barrier = response.data
        assert barrier["reported_by"] == "Test.User"
        assert barrier["created_on"] is not None
        assert barrier["modified_by"] == "Test.User"
        assert barrier["modified_by"] is not None

    def test_barrier_detail_submitted_open_edit_to_resolve(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2

        resolve_barrier_url = reverse("resolve-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={
                "status_date": "2018-09-10",
                "status_summary": "dummy summary",
            },
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 4

    def test_barrier_detail_submitted_open_edit_to_hibernate(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={
                "status_date": "2018-09-10",
                "status_summary": "dummy summary",
            },
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 5

    def test_barrier_detail_submitted_resolved_edit_to_hibernate(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 4

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={
                "status_date": "2018-09-11",
                "status_summary": "dummy summary",
            },
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 5

    def test_barrier_detail_submitted_resolved_edit_to_open(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 4

        resolve_barrier_url = reverse("open-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={
                "status_date": "2018-09-11",
                "status_summary": "dummy summary",
            },
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2

    def test_barrier_detail_edit_barrier_headline_1(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2
        assert response.data["problem_status"] == 2
        assert response.data["barrier_title"] == "Some title"
        assert response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_title": "a different title",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["barrier_title"] == "a different title"
        assert edit_barrier_response.data["problem_status"] == 2
        assert edit_barrier_response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

    def test_barrier_detail_edit_barrier_headline_2(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2
        assert response.data["problem_status"] == 2
        assert response.data["barrier_title"] == "Some title"
        assert response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "problem_status": 1,
                "barrier_title": "a different title",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["barrier_title"] == "a different title"
        assert edit_barrier_response.data["problem_status"] == 1
        assert edit_barrier_response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

    def test_barrier_detail_incorrect_problem_status(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2
        assert response.data["problem_status"] == 2
        assert response.data["barrier_title"] == "Some title"
        assert response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_title": "a different title",
                "problem_status": 3
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_barrier_detail_edit_priority_high(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["priority"]["code"] == "UNKNOWN"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "priority": "HIGH",
                "priority_summary": "some priority summary",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "HIGH"

    def test_barrier_detail_edit_priority_MEDIUM(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["priority"]["code"] == "UNKNOWN"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "priority": "MEDIUM",
                "priority_summary": "some priority summary",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "MEDIUM"

    def test_barrier_detail_edit_priority_low(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["priority"]["code"] == "UNKNOWN"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "priority": "LOW",
                "priority_summary": "some priority summary",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "LOW"


    def test_barrier_detail_edit_priority_and_barrier_type(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["priority"]["code"] == "UNKNOWN"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "priority": "LOW",
                "priority_summary": "some priority summary",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "LOW"

        response = self.api_client.get(get_url)
        assert response.data["barrier_type"] == None

        barrier_type = BarrierType.objects.all()[:1].get()
        edit_type_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_type":barrier_type.id,
                "barrier_type_category":barrier_type.category
            }
        )

        assert edit_type_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert response.data["barrier_type"]["id"] == barrier_type.id
        assert response.data["priority"]["code"] == "LOW"
    
    def test_barrier_detail_edit_barrier_type_then_priority(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["priority"]["code"] == "UNKNOWN"

        response = self.api_client.get(get_url)
        assert response.data["barrier_type"] == None

        barrier_type = BarrierType.objects.all()[:1].get()
        edit_type_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_type":barrier_type.id,
                "barrier_type_category":barrier_type.category
            }
        )

        assert edit_type_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert response.data["barrier_type"]["id"] == barrier_type.id
        assert response.data["priority"]["code"] == "UNKNOWN"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "priority": "LOW",
                "priority_summary": "some priority summary",
            },
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "LOW"

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert response.data["barrier_type"]["id"] == barrier_type.id
        assert response.data["priority"]["code"] == "LOW"

    def test_barrier_detail_next_steps_as_note(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
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
                "next_steps_summary": "Some next steps",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["current_status"]["status"] == 2

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1


    def test_barrier_detail_next_steps_as_note_not_added_400_bad_submit(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "is_resolved": False,
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
                "next_steps_summary": "Some next steps",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_400_BAD_REQUEST

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0
