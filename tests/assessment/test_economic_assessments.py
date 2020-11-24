from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from .factories import EconomicAssessmentFactory
from api.core.test_utils import APITestMixin
from api.metadata.constants import ECONOMIC_ASSESSMENT_RATING
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


class TestEconomicAssessments(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_create_economic_assessment(self, barrier):
        url = reverse("economic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "barrier_id": barrier.id,
                "rating": ECONOMIC_ASSESSMENT_RATING.HIGH,
                "explanation": "Explanation!!!"
            }
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.data["approved"] is None
        assert response.data["archived"] is False
        assert response.data["ready_for_approval"] is False
        assert response.data["barrier_id"] == str(barrier.id)
        assert response.data["rating"]["code"] == ECONOMIC_ASSESSMENT_RATING.HIGH
        assert response.data["explanation"] == "Explanation!!!"
        assert response.data["created_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_create_economic_assessment_with_empty_data(self, barrier):
        url = reverse("economic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data["barrier_id"] == ['This field is required.']
        assert "user_analysis_data" not in response.data
        assert "rating" not in response.data
        assert "explanation" not in response.data

    def test_update_economic_assessment(self, barrier):
        economic_assessment = EconomicAssessmentFactory(
            barrier=barrier,
            rating=ECONOMIC_ASSESSMENT_RATING.HIGH,
        )
        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={
                "rating": ECONOMIC_ASSESSMENT_RATING.LOW,
                "user_analysis_data": "New analysis data",
                "explanation": "New explanation!!!",
            }
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["rating"]["code"] == ECONOMIC_ASSESSMENT_RATING.LOW
        assert response.data["user_analysis_data"] == "New analysis data"
        assert response.data["explanation"] == "New explanation!!!"
        assert response.data["ready_for_approval"] is False
        assert response.data["modified_by"]["id"] == self.user.id

    def test_mark_economic_assessment_as_ready(self, barrier):
        economic_assessment = EconomicAssessmentFactory(barrier=barrier)
        assert economic_assessment.ready_for_approval is False

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"ready_for_approval": True}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["ready_for_approval"] is True
        assert response.data["modified_by"]["id"] == self.user.id

    def test_approve_economic_assessment(self, barrier):
        economic_assessment = EconomicAssessmentFactory(barrier=barrier)
        assert economic_assessment.approved is None

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"approved": True}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["approved"] is True
        assert response.data["reviewed_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_reject_economic_assessment(self, barrier):
        economic_assessment = EconomicAssessmentFactory(barrier=barrier)
        assert economic_assessment.approved is None

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"approved": False}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["approved"] is False
        assert response.data["reviewed_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_archive_economic_assessment(self, barrier):
        economic_assessment = EconomicAssessmentFactory(barrier=barrier)
        assert economic_assessment.archived is False

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"archived": True}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["archived"] is True
        assert response.data["archived_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_auto_archive_economic_assessment(self, barrier):
        economic_assessment = EconomicAssessmentFactory(
            barrier=barrier,
            rating=ECONOMIC_ASSESSMENT_RATING.HIGH,
        )
        assert economic_assessment.archived is False

        url = reverse("economic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "barrier_id": barrier.id,
                "rating": ECONOMIC_ASSESSMENT_RATING.LOW,
                "explanation": "Explanation!!!"
            }
        )
        assert response.status_code == HTTPStatus.CREATED
        economic_assessment.refresh_from_db()
        assert economic_assessment.archived is True

    def test_economic_assessment_detail(self, barrier):
        economic_assessment = EconomicAssessmentFactory(
            barrier=barrier,
            user_analysis_data="Analysis data",
            rating=ECONOMIC_ASSESSMENT_RATING.HIGH,
            explanation="Here's an explanation"
        )

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.get(url)

        assert response.data["user_analysis_data"] == "Analysis data"
        assert response.data["rating"]["code"] == ECONOMIC_ASSESSMENT_RATING.HIGH
        assert response.data["explanation"] == "Here's an explanation"
