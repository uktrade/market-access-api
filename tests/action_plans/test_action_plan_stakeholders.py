from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from api.action_plans.constants import ActionPlanStakeholderStatus
from api.core.test_utils import APITestMixin
from tests.action_plans.factories import ActionPlanStakeholderFactory
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


class TestActionPlanStakeholders(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_create_action_plan_individual_stakeholder(self, barrier):
        url = reverse("action-plans-stakeholders", kwargs={"barrier": barrier.pk})
        data = {
            "is_organisation": False,
        }
        response = self.api_client.post(
            url,
            format="json",
            data=data,
        )

        assert response.status_code == HTTPStatus.CREATED
        stakeholder = barrier.action_plan.stakeholders.first()
        assert stakeholder.action_plan == barrier.action_plan
        assert stakeholder.is_organisation == data["is_organisation"]

    def test_create_action_plan_organisation_stakeholder(self, barrier):
        url = reverse("action-plans-stakeholders", kwargs={"barrier": barrier.pk})
        data = {
            "is_organisation": True,
        }
        response = self.api_client.post(
            url,
            format="json",
            data=data,
        )

        assert response.status_code == HTTPStatus.CREATED
        stakeholder = barrier.action_plan.stakeholders.first()
        assert stakeholder.action_plan == barrier.action_plan
        assert stakeholder.is_organisation == data["is_organisation"]

    def test_add_action_plan_individual_stakeholder_details(self, barrier):
        stakeholder = ActionPlanStakeholderFactory(
            action_plan=barrier.action_plan, is_organisation=False
        )
        url = reverse(
            "action-plans-stakeholders-detail",
            kwargs={"barrier": barrier.pk, "id": stakeholder.pk},
        )
        data = {
            "name": "Nehemiah Bultitude",
            "status": ActionPlanStakeholderStatus.FRIEND,
            "organisation": "Association of Snake Charmers",
            "job_title": "Python Wrangler",
        }
        response = self.api_client.patch(
            url,
            format="json",
            data=data,
        )

        assert response.status_code == HTTPStatus.OK
        stakeholder = barrier.action_plan.stakeholders.first()
        assert stakeholder.is_organisation is False
        assert stakeholder.name == data["name"]
        assert stakeholder.status == data["status"]
        assert stakeholder.organisation == data["organisation"]
        assert stakeholder.job_title == data["job_title"]

    def test_add_action_plan_organisation_stakeholder_details(self, barrier):
        stakeholder = ActionPlanStakeholderFactory(
            action_plan=barrier.action_plan, is_organisation=True
        )
        url = reverse(
            "action-plans-stakeholders-detail",
            kwargs={"barrier": barrier.pk, "id": stakeholder.pk},
        )
        data = {
            "name": "Association of Snake Charmers",
            "status": ActionPlanStakeholderStatus.FRIEND,
        }
        response = self.api_client.patch(
            url,
            format="json",
            data=data,
        )

        assert response.status_code == HTTPStatus.OK
        stakeholder = barrier.action_plan.stakeholders.first()
        assert stakeholder.is_organisation is True
        assert stakeholder.name == data["name"]
        assert stakeholder.status == data["status"]


class TestActionPlanMilestones(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_create_action_plan_milestone(self, barrier):
        url = reverse("action-plans-milestones", kwargs={"barrier": barrier.pk})
        data = {
            "objective": "Do stuff",
        }
        response = self.api_client.post(
            url,
            format="json",
            data=data,
        )

        assert response.status_code == HTTPStatus.CREATED
