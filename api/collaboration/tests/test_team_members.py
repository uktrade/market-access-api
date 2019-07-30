import json
import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from api.barriers.tests.test_utils import TestUtils


class TestListTeamMembers(APITestMixin):
    def test_no_members_except_default(self):
        """Test there are no barrier members using list"""
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

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        response = self.api_client.get(members_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_add_existing_user_as_member(self):
        """Test adding a new member, already existing in the db"""
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = self.api_client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        a_user = create_test_user(
            first_name="Diff", last_name="User", email="diff_user@Useri.com", username=""
        )

        add_mem_response = self.api_client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "email": "diff_user@Useri.com",
                    "first_name": "Diff",
                    "last_name": "User"
                },
                "role": "dummy"
            }
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED
        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 2
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Barrier creator"

        member = mem_response.data["results"][1]
        member["user"]["email"] == "diff_user@Useri.com"
        member["user"]["first_name"] == "Diff"
        member["user"]["last_name"] == "User"
        member["role"] == "dummy"

    def test_add_new_user_as_member(self):
        """Test adding a new member, already existing in the db"""
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = self.api_client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_mem_response = self.api_client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "email": "user1@example.com",
                    "first_name": "first",
                    "last_name": "last"
                },
                "role": "dummy"
            }
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED
        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 2
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Barrier creator"

        member = mem_response.data["results"][1]
        member["user"]["email"] == "user1@example.com"
        member["user"]["first_name"] == "first"
        member["user"]["last_name"] == "last"
        member["role"] == "dummy"

    def test_multiple_members(self):
        """Test adding a new member, already existing in the db"""
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = self.api_client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_mem_response = self.api_client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "email": "user1@example.com",
                    "first_name": "first",
                    "last_name": "last"
                },
                "role": "dummy"
            }
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED

        a_user = create_test_user(
            first_name="Diff", last_name="User", email="diff_user@Useri.com", username=""
        )

        add_mem_response = self.api_client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "email": "diff_user@Useri.com",
                    "first_name": "Diff",
                    "last_name": "User"
                },
                "role": "dummy"
            }
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED

        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 3
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Barrier creator"

        member = mem_response.data["results"][1]
        member["user"]["email"] == "user1@example.com"
        member["user"]["first_name"] == "first"
        member["user"]["last_name"] == "last"
        member["role"] == "dummy"

        member = mem_response.data["results"][2]
        member["user"]["email"] == "diff_user@Useri.com"
        member["user"]["first_name"] == "Diff"
        member["user"]["last_name"] == "User"
        member["role"] == "dummy"

    def test_delete_member(self):
        """Test adding a new member, already existing in the db"""
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
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = self.api_client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_mem_response = self.api_client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "email": "user1@example.com",
                    "first_name": "first",
                    "last_name": "last"
                },
                "role": "dummy"
            }
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED

        a_user = create_test_user(
            first_name="Diff", last_name="User", email="diff_user@Useri.com", username=""
        )

        add_mem_response = self.api_client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "email": "diff_user@Useri.com",
                    "first_name": "Diff",
                    "last_name": "User"
                },
                "role": "dummy"
            }
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED

        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 3
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Barrier creator"

        member = mem_response.data["results"][1]
        member["user"]["email"] == "user1@example.com"
        member["user"]["first_name"] == "first"
        member["user"]["last_name"] == "last"
        member["role"] == "dummy"

        member = mem_response.data["results"][2]
        member["user"]["email"] == "diff_user@Useri.com"
        member["user"]["first_name"] == "Diff"
        member["user"]["last_name"] == "User"
        member["role"] == "dummy"

        mem_id = member["id"]
        get_mem_url = reverse("get-member", kwargs={"pk": mem_id})
        get_mem_response = self.api_client.get(get_mem_url)
        assert get_mem_response.status_code == status.HTTP_200_OK
        assert get_mem_response.data["user"]["email"] == "diff_user@Useri.com"

        delete_mem_response = self.api_client.delete(get_mem_url)
        assert delete_mem_response.status_code == status.HTTP_204_NO_CONTENT

        get_mem_response = self.api_client.get(get_mem_url)
        assert get_mem_response.status_code == status.HTTP_404_NOT_FOUND

        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 2

    def test_delete_default_member(self):
        """Test there are no barrier members using list"""
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

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 1

        member = mem_response.data["results"][0]
        mem_id = member["id"]
        get_mem_url = reverse("get-member", kwargs={"pk": mem_id})
        get_mem_response = self.api_client.get(get_mem_url)
        assert get_mem_response.status_code == status.HTTP_200_OK
        assert get_mem_response.data["user"]["email"] == "Testo@Useri.com"
        assert get_mem_response.data["user"]["first_name"] == "Testo"
        assert get_mem_response.data["user"]["last_name"] == "Useri"
        assert get_mem_response.data["role"] == "Barrier creator"

        delete_mem_response = self.api_client.delete(get_mem_url)
        assert delete_mem_response.status_code == status.HTTP_403_FORBIDDEN

        get_mem_response = self.api_client.get(get_mem_url)
        assert get_mem_response.status_code == status.HTTP_200_OK

        mem_response = self.api_client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 1
