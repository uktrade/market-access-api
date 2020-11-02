from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory
from .factories import StrategicAssessmentFactory

pytestmark = [pytest.mark.django_db]


class TestStrategicAssessments(APITestMixin):
    test_data = {
        "hmg_strategy": "hmg_strategy test",
        "government_policy": "government_policy test",
        "trading_relations": "trading_relations test",
        "uk_interest_and_security": "uk_interest_and_security test",
        "uk_grants": "uk_grants test",
        "competition": "competition test",
        "additional_information": "additional_information test",
        "scale": 4,
    }

    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_create_strategic_assessment(self, barrier):
        url = reverse("strategic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={"barrier_id": barrier.id, **self.test_data}
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.data["approved"] is None
        assert response.data["archived"] is False
        assert response.data["hmg_strategy"] == "hmg_strategy test"
        assert response.data["government_policy"] == "government_policy test"
        assert response.data["trading_relations"] == "trading_relations test"
        assert response.data["uk_interest_and_security"] == "uk_interest_and_security test"
        assert response.data["uk_grants"] == "uk_grants test"
        assert response.data["competition"] == "competition test"
        assert response.data["additional_information"] == "additional_information test"
        assert response.data["scale"]["id"] == 4
        assert response.data["created_by"]["id"] == self.user.id

    def test_create_strategic_assessment_with_empty_data(self, barrier):
        url = reverse("strategic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.data["barrier_id"] == ['This field is required.']
        assert response.data["hmg_strategy"] == ['This field is required.']
        assert response.data["government_policy"] == ['This field is required.']
        assert response.data["trading_relations"] == ['This field is required.']
        assert response.data["uk_interest_and_security"] == ['This field is required.']
        assert response.data["uk_grants"] == ['This field is required.']
        assert response.data["competition"] == ['This field is required.']
        assert response.data["scale"] == ['This field is required.']
        assert "additional_information" not in response.data

    def test_update_strategic_assessment(self, barrier):
        strategic_assessment = StrategicAssessmentFactory(
            barrier=barrier,
            scale=5,
        )
        url = reverse("strategic-assessment-detail", kwargs={"pk": strategic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={
                "scale": "2",
                "hmg_strategy": "New HMG strategy",
                "additional_information": "New info",
            }
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["scale"]["id"] == 2
        assert response.data["hmg_strategy"] == "New HMG strategy"
        assert response.data["additional_information"] == "New info"
        assert response.data["approved"] is None

    def test_approve_strategic_assessment(self, barrier):
        strategic_assessment = StrategicAssessmentFactory(barrier=barrier)
        url = reverse("strategic-assessment-detail", kwargs={"pk": strategic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"approved": True}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["approved"] is True
        assert response.data["reviewed_by"]["id"] == self.user.id

    def test_reject_strategic_assessment(self, barrier):
        strategic_assessment = StrategicAssessmentFactory(barrier=barrier)
        url = reverse("strategic-assessment-detail", kwargs={"pk": strategic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"approved": False}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["approved"] is False
        assert response.data["reviewed_by"]["id"] == self.user.id

    def test_archive_strategic_assessment(self, barrier):
        strategic_assessment = StrategicAssessmentFactory(barrier=barrier)
        url = reverse("strategic-assessment-detail", kwargs={"pk": strategic_assessment.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={"archived": True}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["archived"] is True
        assert response.data["archived_by"]["id"] == self.user.id

    def test_auto_archive_strategic_assessment(self, barrier):
        strategic_assessment = StrategicAssessmentFactory(barrier=barrier,)
        assert strategic_assessment.archived is False

        url = reverse("strategic-assessment-list")
        response = self.api_client.post(
            url,
            format="json",
            data={"barrier_id": barrier.id, **self.test_data}
        )
        assert response.status_code == HTTPStatus.CREATED
        strategic_assessment.refresh_from_db()
        assert strategic_assessment.archived is True

    def test_strategic_assessment_detail(self, barrier):
        strategic_assessment = StrategicAssessmentFactory(
            barrier=barrier,
            **self.test_data,
        )

        url = reverse("strategic-assessment-detail", kwargs={"pk": strategic_assessment.id})
        response = self.api_client.get(url)

        assert response.data["hmg_strategy"] == self.test_data["hmg_strategy"]
        assert response.data["government_policy"] == self.test_data["government_policy"]
        assert response.data["trading_relations"] == self.test_data["trading_relations"]
        assert response.data["uk_interest_and_security"] == self.test_data["uk_interest_and_security"]
        assert response.data["uk_grants"] == self.test_data["uk_grants"]
        assert response.data["competition"] == self.test_data["competition"]
        assert response.data["additional_information"] == self.test_data["additional_information"]
        assert response.data["scale"]["id"] == self.test_data["scale"]
