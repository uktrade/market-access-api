from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin, create_test_user
from api.history.factories import TeamMemberHistoryFactory
from tests.barriers.factories import BarrierFactory
from tests.collaboration.factories import TeamMemberFactory

UserModel = get_user_model()


class TestListTeamMembers(APITestMixin):
    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
    def test_no_members_except_default(self, mock_creator):
        """Test there are no barrier members using list"""
        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        barrier = BarrierFactory(created_by=user)
        TeamMember.objects.create(barrier=barrier, user=user, role="wobble")

        mock_creator.return_value = self.sso_creator

        members_url = reverse("list-members", kwargs={"pk": barrier.id})
        client = self.create_api_client(user=user)
        response = client.get(members_url)
        assert response.status_code == status.HTTP_200_OK
        assert 1 == response.data["count"]

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_id")
    def test_add_existing_user_with_profile_with_sso_user_id_as_member(
        self, mock_sso_user
    ):
        """Test adding a new member, already existing in the db"""
        creator_user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        client = self.create_api_client(creator_user)
        mock_sso_user.return_value = self.sso_user_data_1
        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "term": 2,
                "status_date": "2018-09-10",
                "status": 4,
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "title": "Some title",
                "summary": "Some summary",
                "status_summary": "some status summary",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = Barrier.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        a_user = create_test_user(
            first_name=self.sso_user_data_1["first_name"],
            last_name=self.sso_user_data_1["last_name"],
            email=self.sso_user_data_1["email"],
            username="",
            sso_user_id=self.sso_user_data_1["user_id"],
        )

        add_mem_response = client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "profile": {
                        "sso_user_id": self.sso_user_data_1["user_id"],
                    }
                },
                "role": "dummy",
            },
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED
        mem_response = client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 2
        member = mem_response.data["results"][0]
        assert member["user"]["profile"]["sso_user_id"] == self.sso_creator["user_id"]
        assert member["user"]["email"] == creator_user.email
        assert member["user"]["first_name"] == creator_user.first_name
        assert member["user"]["last_name"] == creator_user.last_name
        assert member["role"] == "Reporter"

        member = mem_response.data["results"][1]
        member["user"]["email"] == self.sso_user_data_1["email"]
        member["user"]["first_name"] == self.sso_user_data_1["first_name"]
        member["user"]["last_name"] == self.sso_user_data_1["last_name"]
        member["role"] == "dummy"

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_id")
    def test_add_existing_user_with_profile_without_sso_user_id_as_member(
        self, mock_sso_user, mock_creator
    ):
        """Test adding a new member, already existing in the db"""
        client = self.api_client
        mock_creator.return_value = self.sso_creator
        mock_sso_user.side_effect = [self.sso_user_data_1, self.sso_user_data_2]
        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "term": 2,
                "status_date": "2018-09-10",
                "status": 4,
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "title": "Some title",
                "summary": "Some summary",
                "status_summary": "some status summary",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = Barrier.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        # create a user and its profle object, but no sso_user_id
        a_user = create_test_user(
            first_name="Diff",
            last_name="User",
            email="diff_user@Useri.com",
            username="",
            internal=True,
        )

        add_mem_response = client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "profile": {
                        "sso_user_id": self.sso_user_data_1["user_id"],
                    }
                },
                "role": "dummy",
            },
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED
        mem_response = client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 2
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Reporter"

        member = mem_response.data["results"][1]
        member["user"]["profile"]["sso_user_id"] == self.sso_user_data_1["user_id"]
        member["user"]["email"] == "diff_user@Useri.com"
        member["user"]["first_name"] == "Diff"
        member["user"]["last_name"] == "User"
        member["role"] == "dummy"

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_id")
    def test_add_existing_user_without_profile_as_member(self, mock_sso_user):
        """Test adding a new member, already existing in the db"""
        client = self.api_client
        mock_sso_user.return_value = self.sso_user_data_1
        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "term": 2,
                "status_date": "2018-09-10",
                "status": 4,
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "title": "Some title",
                "summary": "Some summary",
                "status_summary": "some status summary",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = Barrier.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        # create a user but no profle object
        a_user = create_test_user(
            first_name="Diff",
            last_name="User",
            email="diff_user@Useri.com",
            username="",
        )

        add_mem_response = client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "profile": {
                        "sso_user_id": self.sso_user_data_1["user_id"],
                    }
                },
                "role": "dummy",
            },
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED
        mem_response = client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 2
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Reporter"

        member = mem_response.data["results"][1]
        member["user"]["profile"]["sso_user_id"] == self.sso_user_data_1["user_id"]
        member["user"]["email"] == "diff_user@Useri.com"
        member["user"]["first_name"] == "Diff"
        member["user"]["last_name"] == "User"
        member["role"] == "dummy"

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_id")
    def test_multiple_members(self, mock_sso_user):
        """Test adding a new member, already existing in the db"""
        client = self.api_client
        mock_sso_user.side_effect = [self.sso_user_data_1, self.sso_user_data_2]
        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "term": 2,
                "status_date": "2018-09-10",
                "status": 4,
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "title": "Some title",
                "summary": "Some summary",
                "status_summary": "some status summary",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = Barrier.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        members_url = reverse("list-members", kwargs={"pk": instance.id})
        int_response = client.get(members_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_mem_response = client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "profile": {
                        "sso_user_id": self.sso_user_data_1["user_id"],
                    }
                },
                "role": "dummy",
            },
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED

        a_user = create_test_user(
            first_name="Diff",
            last_name="User",
            email="diff_user@Useri.com",
            username="",
            sso_user_id=self.sso_user_data_2["user_id"],
        )

        add_mem_response = client.post(
            members_url,
            format="json",
            data={
                "user": {
                    "profile": {
                        "sso_user_id": self.sso_user_data_2["user_id"],
                    }
                },
                "role": "dummy",
            },
        )

        assert add_mem_response.status_code == status.HTTP_201_CREATED

        mem_response = client.get(members_url)
        assert mem_response.status_code == status.HTTP_200_OK
        assert mem_response.data["count"] == 3
        member = mem_response.data["results"][0]
        assert member["user"]["email"] == "Testo@Useri.com"
        assert member["user"]["first_name"] == "Testo"
        assert member["user"]["last_name"] == "Useri"
        assert member["role"] == "Reporter"

        member = mem_response.data["results"][1]
        member["user"]["profile"]["sso_user_id"] == self.sso_user_data_1["user_id"]
        member["user"]["email"] == self.sso_user_data_1["email"]
        member["user"]["first_name"] == self.sso_user_data_1["first_name"]
        member["user"]["last_name"] == self.sso_user_data_1["last_name"]
        member["role"] == "dummy"

        member = mem_response.data["results"][2]
        member["user"]["profile"]["sso_user_id"] == self.sso_user_data_2["user_id"]
        member["user"]["email"] == self.sso_user_data_2["email"]
        member["user"]["first_name"] == self.sso_user_data_2["first_name"]
        member["user"]["last_name"] == self.sso_user_data_2["last_name"]
        member["role"] == "dummy"

    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_id")
    def test_add_new_user_as_member(self, mock_sso_user):
        """
        Adding a new user that only exists in SSO. (No django user for them)
        """
        barrier = BarrierFactory()
        mock_sso_user.return_value = self.sso_user_data_1

        assert not TeamMember.objects.count()
        assert not UserModel.objects.filter(email=self.sso_user_data_1)

        payload = {
            "user": {
                "profile": {
                    "sso_user_id": self.sso_user_data_1["user_id"],
                }
            }
        }
        url = reverse("list-members", kwargs={"pk": barrier.id})
        response = self.api_client.post(url, format="json", data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        # Member
        members = TeamMember.objects.filter(barrier=barrier)
        assert 1 == members.count()
        assert "Contributor" == members.first().role
        # Django User
        assert (
            1 == UserModel.objects.filter(email=self.sso_user_data_1["email"]).count()
        )
        user = members.first().user
        assert self.sso_user_data_1["email"] == user.email
        assert self.sso_user_data_1["first_name"] == user.first_name
        assert self.sso_user_data_1["last_name"] == user.last_name

    def test_delete_member(self):
        user1 = create_test_user()
        barrier = BarrierFactory(created_by=user1)
        member = TeamMemberFactory(barrier=barrier, user=user1, role="Contributor")
        url = reverse("get-member", kwargs={"pk": member.id})

        assert 1 == TeamMember.objects.filter(barrier=barrier).count()

        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert 0 == TeamMember.objects.filter(barrier=barrier).count()

    def test_delete_default_member(self):
        """
        Cannot delete a member if default is set to True.
        """
        user1 = create_test_user()
        barrier = BarrierFactory(created_by=user1)
        member = TeamMemberFactory(
            barrier=barrier, user=user1, role="Protected role", default=True
        )
        url = reverse("get-member", kwargs={"pk": member.id})

        assert 1 == TeamMember.objects.filter(barrier=barrier).count()

        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 1 == TeamMember.objects.filter(barrier=barrier).count()

    def test_change_owner(self):
        user1 = create_test_user()
        user2 = create_test_user()
        barrier = BarrierFactory(created_by=user1)
        TeamMemberFactory(barrier=barrier, user=user1, role="Reporter", default=True)
        member = TeamMemberFactory(
            barrier=barrier, user=user1, role="Owner", default=True
        )
        url = reverse("get-member", kwargs={"pk": member.id})

        assert user1 == member.user

        payload = {"user": user2.profile.sso_user_id}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        member.refresh_from_db()
        assert user2 == member.user

    def test_change_owner__history_items(self):
        user1 = create_test_user()
        user2 = create_test_user()
        barrier = BarrierFactory(created_by=user1)
        TeamMemberFactory(barrier=barrier, user=user1, role="Reporter", default=True)
        member = TeamMemberFactory(
            barrier=barrier, user=user1, role="Owner", default=True
        )
        url = reverse("get-member", kwargs={"pk": member.id})

        assert user1 == member.user
        items = TeamMemberHistoryFactory.get_history_items(barrier_id=barrier.pk)
        assert 2 == len(items)

        payload = {"user": user2.profile.sso_user_id}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        items = TeamMemberHistoryFactory.get_history_items(barrier_id=barrier.pk)
        assert 3 == len(items)
        assert user1 == items[-1].old_record.user
        assert user2 == items[-1].new_record.user
        assert "Owner" == items[-1].old_record.role
        assert "Owner" == items[-1].new_record.role

    def test_change_reporter_forbidden(self):
        user1 = create_test_user()
        user2 = create_test_user()
        barrier = BarrierFactory(created_by=user1)
        member = TeamMemberFactory(
            barrier=barrier, user=user1, role="Reporter", default=True
        )
        url = reverse("get-member", kwargs={"pk": member.id})

        assert user1 == member.user

        payload = {"user": user2.id}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_403_FORBIDDEN == response.status_code
        member.refresh_from_db()
        assert user1 == member.user

    def test_change_contributor_forbidden(self):
        user1 = create_test_user()
        user2 = create_test_user()
        barrier = BarrierFactory(created_by=user1)
        member = TeamMemberFactory(barrier=barrier, user=user1, role="Contributor")
        url = reverse("get-member", kwargs={"pk": member.id})

        assert user1 == member.user

        payload = {"user": user2.id}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_403_FORBIDDEN == response.status_code
        member.refresh_from_db()
        assert user1 == member.user
