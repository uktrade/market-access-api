from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory

from .factories import ResolvabilityAssessmentFactory

pytestmark = [pytest.mark.django_db]


class TestResolvabilityAssessments(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_create_resolvability_assessment(self, barrier):
        url = reverse("resolvability-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "barrier_id": barrier.id,
                "effort_to_resolve": "4",
                "time_to_resolve": "2",
                "explanation": "Explanation!!!",
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.data["approved"] is None
        assert response.data["archived"] is False
        assert response.data["barrier_id"] == str(barrier.id)
        assert response.data["effort_to_resolve"]["id"] == 4
        assert response.data["time_to_resolve"]["id"] == 2
        assert response.data["explanation"] == "Explanation!!!"
        assert response.data["created_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_create_resolvability_assessment_with_empty_data(self, barrier):
        url = reverse("resolvability-assessment-list")
        response = self.api_client.post(url, format="json", data={})
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data["barrier_id"] == ["This field is required."]
        assert response.data["effort_to_resolve"] == ["This field is required."]
        assert response.data["time_to_resolve"] == ["This field is required."]
        assert "explanation" not in response.data

    def test_update_resolvability_assessment(self, barrier):
        resolvability_assessment = ResolvabilityAssessmentFactory(
            barrier=barrier,
            time_to_resolve=1,
            effort_to_resolve=1,
        )
        url = reverse(
            "resolvability-assessment-detail",
            kwargs={"pk": resolvability_assessment.id},
        )
        response = self.api_client.patch(
            url,
            format="json",
            data={
                "effort_to_resolve": "4",
                "time_to_resolve": "3",
                "explanation": "New explanation!!!",
            },
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["effort_to_resolve"]["id"] == 4
        assert response.data["time_to_resolve"]["id"] == 3
        assert response.data["explanation"] == "New explanation!!!"
        assert response.data["approved"] is None
        assert response.data["modified_by"]["id"] == self.user.id

    def test_approve_resolvability_assessment(self, barrier):
        resolvability_assessment = ResolvabilityAssessmentFactory(barrier=barrier)
        url = reverse(
            "resolvability-assessment-detail",
            kwargs={"pk": resolvability_assessment.id},
        )
        response = self.api_client.patch(url, format="json", data={"approved": True})
        assert response.status_code == HTTPStatus.OK
        assert response.data["approved"] is True
        assert response.data["reviewed_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_reject_resolvability_assessment(self, barrier):
        resolvability_assessment = ResolvabilityAssessmentFactory(barrier=barrier)
        url = reverse(
            "resolvability-assessment-detail",
            kwargs={"pk": resolvability_assessment.id},
        )
        response = self.api_client.patch(url, format="json", data={"approved": False})
        assert response.status_code == HTTPStatus.OK
        assert response.data["approved"] is False
        assert response.data["reviewed_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_archive_resolvability_assessment(self, barrier):
        resolvability_assessment = ResolvabilityAssessmentFactory(barrier=barrier)
        url = reverse(
            "resolvability-assessment-detail",
            kwargs={"pk": resolvability_assessment.id},
        )
        response = self.api_client.patch(url, format="json", data={"archived": True})
        assert response.status_code == HTTPStatus.OK
        assert response.data["archived"] is True
        assert response.data["archived_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_auto_archive_resolvability_assessment(self, barrier):
        resolvability_assessment = ResolvabilityAssessmentFactory(
            barrier=barrier,
            time_to_resolve=1,
            effort_to_resolve=1,
        )
        assert resolvability_assessment.archived is False

        url = reverse("resolvability-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "barrier_id": barrier.id,
                "effort_to_resolve": "4",
                "time_to_resolve": "2",
                "explanation": "Explanation!!!",
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        resolvability_assessment.refresh_from_db()
        assert resolvability_assessment.archived is True

    def test_resolvability_assessment_detail(self, barrier):
        resolvability_assessment = ResolvabilityAssessmentFactory(
            barrier=barrier,
            time_to_resolve=1,
            effort_to_resolve=1,
            explanation="Here's an explanation",
        )

        url = reverse(
            "resolvability-assessment-detail",
            kwargs={"pk": resolvability_assessment.id},
        )
        response = self.api_client.get(url)

        assert response.data["effort_to_resolve"]["id"] == 1
        assert response.data["time_to_resolve"]["id"] == 1
        assert response.data["explanation"] == "Here's an explanation"
