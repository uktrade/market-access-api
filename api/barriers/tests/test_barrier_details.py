from rest_framework import status
from rest_framework.reverse import reverse

from freezegun import freeze_time

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
                "resolved_status": 4,
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
                "resolved_status": 4,
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
        assert barrier["status"]["id"] == 4
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
                "resolved_status": 4,
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
                "resolved_status": 4,
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
                "resolved_status": 4,
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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 4

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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 5

    def test_barrier_detail_submitted_resolved_edit_to_hibernate(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
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
        assert response.data["status"]["id"] == 4

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-11", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 5

    def test_barrier_detail_submitted_open_edit_to_unknown(self):
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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("unknown-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 0

    def test_barrier_detail_submitted_resolved_edit_to_unknown(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
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
        assert response.data["status"]["id"] == 4

        unknown_barrier_url = reverse("unknown-barrier", kwargs={"pk": instance.id})
        unknown_barrier_response = self.api_client.put(
            unknown_barrier_url,
            format="json",
            data={"status_date": "2018-09-11", "status_summary": "dummy summary"},
        )
        assert unknown_barrier_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 0

    def test_barrier_detail_submitted_resolved_edit_to_open(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
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
        assert response.data["status"]["id"] == 4

        resolve_barrier_url = reverse("open-in-progress", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-11", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 2

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
        assert response.data["status"]["id"] == 2
        assert response.data["problem_status"] == 2
        assert response.data["barrier_title"] == "Some title"
        assert response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

        edit_barrier_response = self.api_client.put(
            get_url, format="json", data={"barrier_title": "a different title"}
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["barrier_title"] == "a different title"
        assert edit_barrier_response.data["problem_status"] == 2
        assert (
            edit_barrier_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )

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
        assert response.data["status"]["id"] == 2
        assert response.data["problem_status"] == 2
        assert response.data["barrier_title"] == "Some title"
        assert response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={"problem_status": 1, "barrier_title": "a different title"},
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["barrier_title"] == "a different title"
        assert edit_barrier_response.data["problem_status"] == 1
        assert (
            edit_barrier_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )

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
        assert response.data["status"]["id"] == 2
        assert response.data["problem_status"] == 2
        assert response.data["barrier_title"] == "Some title"
        assert response.data["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"

    def test_barrier_detail_conflicting_all_sectors(self):
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
        assert response.data["status"]["id"] == 2
        assert response.data["sectors_affected"] == True
        assert len(response.data["sectors"]) == 2

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={"all_sectors": True},
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK

    def test_barrier_detail_conflicting_sectors(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "all_sectors": True,
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
        assert response.data["status"]["id"] == 2
        assert response.data["sectors_affected"] == True

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={"sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ]},
            )

        assert edit_barrier_response.status_code == status.HTTP_200_OK

    def test_barrier_detail_missing_all_sectors_and_sectors(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
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
        assert submit_response.status_code == status.HTTP_400_BAD_REQUEST

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
            data={"priority": "HIGH", "priority_summary": "some priority summary"},
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
            data={"priority": "MEDIUM", "priority_summary": "some priority summary"},
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
            data={"priority": "LOW", "priority_summary": "some priority summary"},
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "LOW"

    def test_barrier_detail_edit_barrier_types(self):
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
        assert len(response.data["barrier_types"]) == 0

        db_barrier_types = BarrierType.objects.all()[:2]
        barrier_type_ids = [bt.id for bt in db_barrier_types]
        edit_type_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_types": barrier_type_ids
            },
        )

        assert edit_type_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert response.data["barrier_types"] == barrier_type_ids

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
            data={"priority": "LOW", "priority_summary": "some priority summary"},
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "LOW"

        response = self.api_client.get(get_url)
        assert len(response.data["barrier_types"]) == 0

        db_barrier_types = BarrierType.objects.all()[:2]
        edit_type_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_types": [bt.id for bt in db_barrier_types]
            },
        )

        assert edit_type_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert response.data["barrier_types"] is not None
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
        assert len(response.data["barrier_types"]) == 0

        db_barrier_types = BarrierType.objects.all()[:2]
        edit_type_response = self.api_client.put(
            get_url,
            format="json",
            data={
                "barrier_types": [bt.id for bt in db_barrier_types]
            },
        )

        assert edit_type_response.status_code == status.HTTP_200_OK

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert len(response.data["barrier_types"]) == 2
        assert response.data["priority"]["code"] == "UNKNOWN"

        edit_barrier_response = self.api_client.put(
            get_url,
            format="json",
            data={"priority": "LOW", "priority_summary": "some priority summary"},
        )

        assert edit_barrier_response.status_code == status.HTTP_200_OK
        assert edit_barrier_response.data["id"] == str(instance.id)
        assert edit_barrier_response.data["priority"]["code"] == "LOW"

        response = self.api_client.get(get_url)
        assert response.data["id"] == str(instance.id)
        assert len(response.data["barrier_types"]) == 2
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
        assert response.data["status"]["id"] == 2

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

    def test_barrier_detail_submitted_open_and_resolve_edit_status_summary(self):
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["id"] == str(instance.id)
        assert get_response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        resolve_response = self.api_client.get(get_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["id"] == str(instance.id)
        assert resolve_response.data["status"]["id"] == 4
        assert resolve_response.data["status"]["summary"] == "dummy summary"
        assert resolve_response.data["status"]["date"] == "2018-09-10"

    def test_barrier_detail_submitted_open_and_resolve_edit_summary_no_status_date_400(self):
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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 4
        assert response.data["status"]["summary"] == "dummy summary"

    def test_barrier_detail_submitted_open_and_resolve_edit_status_no_status_summary_400(self):
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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 4
        assert response.data["status"]["summary"] == "dummy summary"

    @freeze_time("2018-11-10")
    def test_barrier_detail_submitted_open_and_hibernate_edit_status_summary_1(self):
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["id"] == str(instance.id)
        assert get_response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_summary": "dummy summary"},
        )

        resolve_response = self.api_client.get(get_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["id"] == str(instance.id)
        assert resolve_response.data["status"]["id"] == 5
        assert resolve_response.data["status"]["summary"] == "dummy summary"
        assert resolve_response.data["status"]["date"] == "2018-11-10"

    @freeze_time("2018-11-10")
    def test_barrier_detail_submitted_open_and_hibernate_edit_status_summary_2(self):
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["id"] == str(instance.id)
        assert get_response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_summary": "dummy summary"},
        )

        resolve_response = self.api_client.get(get_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["id"] == str(instance.id)
        assert resolve_response.data["status"]["id"] == 5
        assert resolve_response.data["status"]["summary"] == "dummy summary"
        assert resolve_response.data["status"]["date"] == "2018-11-10"

    @freeze_time("2018-11-10")
    def test_barrier_detail_submitted_open_and_hibernate_edit_status_summary_2(self):
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["id"] == str(instance.id)
        assert get_response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_summary": "dummy summary"},
        )

        resolve_response = self.api_client.get(get_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["id"] == str(instance.id)
        assert resolve_response.data["status"]["id"] == 5
        assert resolve_response.data["status"]["summary"] == "dummy summary"
        assert resolve_response.data["status"]["date"] == "2018-11-10"

    @freeze_time("2018-11-10")
    def test_barrier_detail_submitted_open_and_hibernate_edit_status_summary_and_status_date(self):
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["id"] == str(instance.id)
        assert get_response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        resolve_response = self.api_client.get(get_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["id"] == str(instance.id)
        assert resolve_response.data["status"]["id"] == 5
        assert resolve_response.data["status"]["summary"] == "dummy summary"
        assert resolve_response.data["status"]["date"] == "2018-11-10"

    @freeze_time("2018-11-10")
    def test_barrier_detail_submitted_open_and_hibernate_edit_summary_no_status_date_400(self):
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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 5
        assert response.data["status"]["summary"] == "dummy summary"

    def test_barrier_detail_submitted_open_and_hibernate_edit_status_no_status_summary_400(self):
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
        assert response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("hibernate-barrier", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(instance.id)
        assert response.data["status"]["id"] == 5
        assert response.data["status"]["summary"] == "dummy summary"

    def test_barrier_detail_submitted_open_and_resolve_edit_status_ignore(self):
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["id"] == str(instance.id)
        assert get_response.data["status"]["id"] == 2

        resolve_barrier_url = reverse("resolve-in-full", kwargs={"pk": instance.id})
        resolve_barrier_response = self.api_client.put(
            resolve_barrier_url,
            format="json",
            data={"status_date": "2018-09-10", "status_summary": "dummy summary"},
        )

        resolve_response = self.api_client.get(get_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["id"] == str(instance.id)
        assert resolve_response.data["status"]["id"] == 4
        assert resolve_response.data["status"]["summary"] == "dummy summary"
        assert resolve_response.data["status"]["date"] == "2018-09-10"

    def test_barrier_with_report_resolved_in_full(self):
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
                "resolved_status": 4,
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
        assert barrier["status"]["id"] == 4

    def test_barrier_with_report_resolved_in_part(self):
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
                "resolved_status": 3,
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
        assert barrier["status"]["id"] == 3
