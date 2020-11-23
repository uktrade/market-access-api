from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from .factories import EconomicAssessmentFactory, EconomicImpactAssessmentFactory
from api.core.test_utils import APITestMixin
from api.metadata.constants import ECONOMIC_ASSESSMENT_RATING
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


class TestEconomicImpactAssessments(APITestMixin):
    @pytest.fixture
    def economic_assessment(self):
        barrier = BarrierFactory()
        return EconomicAssessmentFactory(
            barrier=barrier,
            rating=ECONOMIC_ASSESSMENT_RATING.HIGH,
        )

    def test_create_economic_impact_assessment(self, economic_assessment):
        url = reverse("economic-impact-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "economic_assessment_id": economic_assessment.id,
                "impact": "1",
                "explanation": "Explanation!!!"
            }
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.data["archived"] is False
        assert response.data["economic_assessment_id"] == economic_assessment.id
        assert response.data["impact"]["id"] == 1
        assert response.data["explanation"] == "Explanation!!!"
        assert response.data["created_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_create_economic_impact_assessment_with_empty_data(self):
        url = reverse("economic-impact-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data["economic_assessment_id"] == ['This field is required.']
        assert response.data["impact"] == ['This field is required.']
        assert "explanation" not in response.data

    def test_update_economic_impact_assessment(self, economic_assessment):
        economic_impact_assessment = EconomicImpactAssessmentFactory(
            economic_assessment=economic_assessment,
            impact=4,
        )
        url = reverse("economic-impact-assessment-detail", kwargs={"pk": economic_impact_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={
                "impact": "7",
                "explanation": "New explanation!!!"
            }
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["impact"]["id"] == 7
        assert response.data["explanation"] == "New explanation!!!"
        assert response.data["modified_by"]["id"] == self.user.id

    def test_archive_economic_impact_assessment(self, economic_assessment):
        economic_impact_assessment = EconomicImpactAssessmentFactory(
            economic_assessment=economic_assessment,
            impact=4,
        )
        url = reverse("economic-impact-assessment-detail", kwargs={"pk": economic_impact_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"archived": True}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["archived"] is True
        assert response.data["archived_by"]["id"] == self.user.id
        assert response.data["modified_by"]["id"] == self.user.id

    def test_auto_archive_economic_impact_assessment(self, economic_assessment):
        """
        Ensure all of the barrier's existing economic impact assessments are archived
        when a new one is created.
        """
        economic_impact_assessment1 = EconomicImpactAssessmentFactory(
            economic_assessment=economic_assessment,
            impact=4,
        )
        economic_assessment2 = EconomicAssessmentFactory(
            barrier=economic_assessment.barrier,
            rating=ECONOMIC_ASSESSMENT_RATING.LOW,
        )
        economic_impact_assessment2 = EconomicImpactAssessmentFactory(
            economic_assessment=economic_assessment2,
            impact=5,
        )
        assert economic_impact_assessment1.archived is False
        assert economic_impact_assessment2.archived is False

        url = reverse("economic-impact-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "economic_assessment_id": economic_assessment2.id,
                "impact": "1",
                "explanation": "Explanation!!!"
            }
        )
        assert response.status_code == HTTPStatus.CREATED
        economic_impact_assessment1.refresh_from_db()
        economic_impact_assessment2.refresh_from_db()
        assert economic_impact_assessment1.archived is True
        assert economic_impact_assessment2.archived is True

    def test_economic_impact_assessment_detail(self, economic_assessment):
        economic_impact_assessment = EconomicImpactAssessmentFactory(
            economic_assessment=economic_assessment,
            impact=7,
            explanation="Here's an explanation",
        )

        url = reverse("economic-impact-assessment-detail", kwargs={"pk": economic_impact_assessment.id})
        response = self.api_client.get(url)

        assert response.data["impact"]["id"] == 7
        assert response.data["explanation"] == "Here's an explanation"
