from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.barriers.models import BarrierProgressUpdate, ProgrammeFundProgressUpdate
from api.core.test_utils import APITestMixin
from api.metadata.constants import PROGRESS_UPDATE_CHOICES
from tests.barriers.factories import BarrierFactory


class TestTop100ProgressUpdates(APITestMixin, TestCase):
    def test_create_top_100_progress_update(self):
        barrier = BarrierFactory()
        url = reverse("top_100_progress_updates", kwargs={"barrier_pk": barrier.id})
        data = {
            "barrier": barrier.id,
            "status": PROGRESS_UPDATE_CHOICES.ON_TRACK,
            "message": "Test update",
            "next_steps": "Test next steps",
        }
        response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == data["status"]
        assert response.data["message"] == data["message"]
        assert response.data["next_steps"] == data["next_steps"]

    def test_update_top_100_progress_update(self):
        barrier = BarrierFactory()
        barrier_update = BarrierProgressUpdate.objects.create(
            barrier=barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Test update",
            next_steps="Test next steps",
        )
        url = reverse(
            "top_100_progress_updates_detail",
            kwargs={"pk": barrier_update.pk, "barrier_pk": barrier.pk},
        )
        data = {
            "status": PROGRESS_UPDATE_CHOICES.RISK_OF_DELAY,
            "message": "Test update is updated",
            "next_steps": "Test next steps is updated",
        }
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == data["status"]
        assert response.data["message"] == data["message"]
        assert response.data["next_steps"] == data["next_steps"]


class TestProgrammeFundProgressUpdates(APITestMixin, TestCase):
    def test_create_programme_fund_progress_update(self):
        barrier = BarrierFactory()
        url = reverse(
            "programme_fund_progress_updates", kwargs={"barrier_pk": barrier.id}
        )
        data = {
            "barrier": barrier.id,
            "milestones_and_deliverables": "Test milestones and deliverables",
            "expenditure": "Test expenditure",
        }
        response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert (
            response.data["milestones_and_deliverables"]
            == data["milestones_and_deliverables"]
        )
        assert response.data["expenditure"] == data["expenditure"]

    def test_update_programme_fund_progress_update(self):
        barrier = BarrierFactory()
        barrier_update = ProgrammeFundProgressUpdate.objects.create(
            barrier=barrier,
            milestones_and_deliverables="Test milestones and deliverables",
            expenditure="Test expenditure",
        )
        url = reverse(
            "programme_fund_progress_updates_detail",
            kwargs={"pk": barrier_update.pk, "barrier_pk": barrier.pk},
        )
        data = {
            "status": PROGRESS_UPDATE_CHOICES.RISK_OF_DELAY,
            "milestones_and_deliverables": "Test milestones and deliverables is updated",
            "expenditure": "Test expenditure is updated",
        }
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["milestones_and_deliverables"]
            == data["milestones_and_deliverables"]
        )
        assert response.data["expenditure"] == data["expenditure"]
