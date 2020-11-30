from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin, create_test_user
from tests.barriers.factories import BarrierFactory


class BarrierModifiedByTestCase(APITestMixin, APITestCase):
    """
    Updating models related to a barrier should update the barrier's modified_by value
    """
    def setUp(self):
        self.barrier = BarrierFactory()
        self.user1 = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        self.user2 = create_test_user(sso_user_id=self.sso_user_data_2["user_id"])
        self.api_client1 = self.create_api_client(user=self.user1)
        self.api_client2 = self.create_api_client(user=self.user2)

    def test_note_changes_barrier_modified_by(self):
        assert self.barrier.modified_by != self.user1

        # Create a note
        create_url = reverse("list-interactions", kwargs={"pk": self.barrier.id})
        response = self.api_client1.post(create_url, json={"text": "note"})
        assert response.status_code == status.HTTP_201_CREATED
        interaction_id = response.data.get("id")

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user1

        # Update the note
        update_url = reverse("get-interaction", kwargs={"pk": interaction_id})
        response = self.api_client2.patch(update_url, json={"text": "updated note"})
        assert response.status_code == status.HTTP_200_OK

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user2

    def test_assessment_changes_barrier_modified_by(self):
        assert self.barrier.modified_by != self.user1

        # Create an assessment
        url = reverse("economic-assessment-list")
        response = self.api_client1.post(url, data={"barrier_id": self.barrier.id, "rating": "HIGH"})

        assert response.status_code == status.HTTP_201_CREATED
        assessment_id = response.data.get("id")

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user1

        # Update the assessment
        url = reverse("economic-assessment-detail", kwargs={"pk": assessment_id})
        response = self.api_client2.patch(url, data={"rating": "MEDIUMLOW"})

        assert response.status_code == status.HTTP_200_OK

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user2

    def test_team_member_changes_barrier_modified_by(self):
        assert self.barrier.modified_by != self.user1

        # Create a new team member
        create_url = reverse("list-members", kwargs={"pk": self.barrier.id})
        response = self.api_client1.post(
            create_url,
            format="json",
            data={
                "user": {"profile": {"sso_user_id": self.user1.profile.sso_user_id}},
                "role": "Contributor",
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        team_member_id = response.data.get("id")

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user1

        # Update the team member - only allowed to change the owner role
        TeamMember.objects.filter(pk=team_member_id).update(role="Owner")
        update_url = reverse("get-member", kwargs={"pk": team_member_id})
        response = self.api_client2.patch(
            update_url,
            format="json",
            data={"user": self.user2.profile.sso_user_id}
        )
        assert response.status_code == status.HTTP_200_OK

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user2

    def test_wto_changes_barrier_modified_by(self):
        assert self.barrier.modified_by != self.user1

        # Update WTO information
        url = reverse("get-barrier", kwargs={"pk": self.barrier.id})
        response = self.api_client1.patch(
            url,
            json={"wto_profile": {"case_number": {"ABC123"}},}
        )
        assert response.status_code == status.HTTP_200_OK

        self.barrier.refresh_from_db()
        assert self.barrier.modified_by == self.user1
