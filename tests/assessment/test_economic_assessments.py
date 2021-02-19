from http import HTTPStatus

import pytest
from mock import patch
from rest_framework.reverse import reverse

from api.assessment.automate.calculator import AssessmentCalculator
from api.assessment.automate.exceptions import CountryNotFound
from api.core.test_utils import APITestMixin
from api.interactions.models import Document
from api.metadata.constants import ECONOMIC_ASSESSMENT_RATING
from tests.barriers.factories import BarrierFactory

from .factories import EconomicAssessmentFactory

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
        assert "rating" not in response.data
        assert "explanation" not in response.data

    def test_update_economic_assessment(self, barrier):
        economic_assessment = EconomicAssessmentFactory(
            barrier=barrier,
            rating=ECONOMIC_ASSESSMENT_RATING.HIGH,
        )
        document = Document.objects.create(original_filename="test.jpg")

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={
                "rating": ECONOMIC_ASSESSMENT_RATING.LOW,
                "explanation": "New explanation!!!",
                "documents": [str(document.id)],
            }
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["rating"]["code"] == ECONOMIC_ASSESSMENT_RATING.LOW
        assert len(response.data["documents"]) == 1
        assert response.data["documents"][0]["id"] == document.id
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
            rating=ECONOMIC_ASSESSMENT_RATING.HIGH,
            explanation="Here's an explanation"
        )

        url = reverse("economic-assessment-detail", kwargs={"pk": economic_assessment.id})
        response = self.api_client.get(url)

        assert response.data["rating"]["code"] == ECONOMIC_ASSESSMENT_RATING.HIGH
        assert response.data["explanation"] == "Here's an explanation"

    @patch.object(AssessmentCalculator, "calculate")
    def test_automated_economic_assessment(self, mock_calculate, barrier):
        mock_calculate.return_value = {"test": "data"}
        url = reverse("economic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "barrier_id": barrier.id,
                "automate": True,
            }
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.data["automated_analysis_data"] == {'test': 'data'}
        assert response.data["approved"] is None
        assert response.data["archived"] is False
        assert response.data["ready_for_approval"] is False
        assert response.data["barrier_id"] == str(barrier.id)
        assert response.data["rating"] is None
        assert response.data["explanation"] == ""
        assert response.data["created_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    @patch.object(AssessmentCalculator, "calculate")
    def test_automated_economic_assessment_error(self, mock_calculate, barrier):
        mock_calculate.side_effect = CountryNotFound("Country not found: USA")

        url = reverse("economic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "barrier_id": barrier.id,
                "automate": True,
            }
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert str(response.data[0]) == "Country not found: USA"
