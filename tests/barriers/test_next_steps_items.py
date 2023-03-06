from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.barriers.models import BarrierNextStepItem
from api.core.test_utils import APITestMixin
from api.metadata.constants import NEXT_STEPS_ITEMS_STATUS_CHOICES
from tests.barriers.factories import BarrierFactory


class TestNextStepsItems(APITestMixin, TestCase):
    def test_create_next_steps_item(self):
        barrier = BarrierFactory()
        url = reverse("next_steps_items", kwargs={"barrier_pk": barrier.id})
        data = {
            "barrier": barrier.id,
            "status": NEXT_STEPS_ITEMS_STATUS_CHOICES.IN_PROGRESS,
            "next_step_owner": "Test Owner",
            "next_step_item": "Test next step item",
        }
        response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == data["status"]
        assert response.data["next_step_owner"] == data["next_step_owner"]
        assert response.data["next_step_item"] == data["next_step_item"]

    def test_update_next_steps_item(self):
        barrier = BarrierFactory()
        next_step_update = BarrierNextStepItem.objects.create(
            barrier=barrier,
            status=NEXT_STEPS_ITEMS_STATUS_CHOICES.IN_PROGRESS,
            next_step_owner="Test Owner",
            next_step_item="Test next step item",
        )
        url = reverse(
            "next_steps_items_detail",
            kwargs={"pk": next_step_update.pk, "barrier_pk": barrier.pk},
        )
        data = {
            "status": NEXT_STEPS_ITEMS_STATUS_CHOICES.COMPLETED,
            "next_step_owner": "Test Owner updated",
            "next_step_item": "Test next step item updated",
        }
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == data["status"]
        assert response.data["next_step_owner"] == data["next_step_owner"]
        assert response.data["next_step_item"] == data["next_step_item"]
