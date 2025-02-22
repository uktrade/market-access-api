import datetime
from datetime import timedelta
from unittest import TestCase

from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import EstimatedResolutionDateRequest
from api.core.test_utils import APITestMixin
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS
from tests.barriers.factories import BarrierFactory


class TestBarrierDownloadViews(APITestMixin, TestCase):

    def setUp(self):
        super().setUp()

    def test_create_erd_request_not_in_future_400(self):
        barrier = BarrierFactory(estimated_resolution_date=None)
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})
        data = {"estimated_resolution_date": datetime.date.today() - timedelta(days=31), "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'estimated_resolution_date': ['Must be in future']}

    def test_create_erd_request_no_date_201(self):
        barrier = BarrierFactory(estimated_resolution_date=None)
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})
        data = {"estimated_resolution_date": datetime.date.today() + timedelta(days=31), "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        barrier.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert not barrier.get_active_erd_request()
        assert barrier.estimated_resolution_date == data["estimated_resolution_date"]

    def test_create_erd_has_existing_erd_request(self):
        barrier = BarrierFactory(estimated_resolution_date=datetime.date.today())
        EstimatedResolutionDateRequest.objects.create(
            barrier=barrier,
            estimated_resolution_date=datetime.date.today() + timedelta(days=100),
            reason="test",
            status=EstimatedResolutionDateRequest.STATUSES.NEEDS_REVIEW
        )

        assert barrier.get_active_erd_request()

        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})
        data = {"estimated_resolution_date": datetime.date.today() + timedelta(days=31), "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        barrier.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert not barrier.get_active_erd_request()

    def test_create_erd_same_date_200(self):
        date = datetime.date.today() + timedelta(days=100)
        barrier = BarrierFactory(estimated_resolution_date=date)

        assert not barrier.get_active_erd_request()

        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})
        data = {"estimated_resolution_date": date, "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_priority_create_erd_request_no_date_201(self):
        priority_barrier = BarrierFactory(
            estimated_resolution_date=None, top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED
        )
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": priority_barrier.id})
        data = {"estimated_resolution_date": datetime.date.today() + timedelta(days=31), "reason": "Test Reason"}

        assert not priority_barrier.get_active_erd_request()

        response = self.api_client.post(url, data=data, format="json")

        priority_barrier.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert not priority_barrier.get_active_erd_request()
        assert priority_barrier.estimated_resolution_date == data["estimated_resolution_date"]

    def test_priority_create_erd_request_later_date_201(self):
        priority_barrier = BarrierFactory(
            estimated_resolution_date=datetime.date.today(), top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED
        )
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": priority_barrier.id})
        data = {"estimated_resolution_date": datetime.date.today() + timedelta(days=31), "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        priority_barrier.refresh_from_db()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()
        assert priority_barrier.estimated_resolution_date != data["estimated_resolution_date"]

    def test_priority_create_erd_request_earlier_date_200(self):
        priority_barrier = BarrierFactory(
            estimated_resolution_date=datetime.date.today() + timedelta(days=90),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED
        )
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": priority_barrier.id})
        data = {"estimated_resolution_date": datetime.date.today() + timedelta(days=32), "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        priority_barrier.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert not priority_barrier.get_active_erd_request()
        assert priority_barrier.estimated_resolution_date == data["estimated_resolution_date"]

    def test_remove_erd_request_200(self):
        barrier = BarrierFactory(
            estimated_resolution_date=datetime.date.today() + timedelta(days=31),
        )
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})
        data = {"estimated_resolution_date": None, "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        barrier.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert not barrier.get_active_erd_request()
        assert not barrier.estimated_resolution_date

    def test_priority_remove_erd_request_201(self):
        priority_barrier = BarrierFactory(
            estimated_resolution_date=datetime.date.today() + timedelta(days=31),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED
        )
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": priority_barrier.id})
        data = {"estimated_resolution_date": None, "reason": "Test Reason"}

        response = self.api_client.post(url, data=data, format="json")

        priority_barrier.refresh_from_db()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()
        assert priority_barrier.estimated_resolution_date

    def test_get_erd_request_200(self):
        barrier = BarrierFactory(
            estimated_resolution_date=datetime.date.today() + timedelta(days=31),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED
        )
        erd_request = EstimatedResolutionDateRequest.objects.create(
            barrier=barrier,
            estimated_resolution_date=datetime.date.today() + timedelta(days=100),
            reason="test",
            status=EstimatedResolutionDateRequest.STATUSES.NEEDS_REVIEW
        )
        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})

        response = self.api_client.get(url, format="json")
        data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert data["status"] == "NEEDS_REVIEW"

    def test_get_erd_request_404(self):
        barrier = BarrierFactory(
            estimated_resolution_date=datetime.date.today() + timedelta(days=31),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED
        )

        url = reverse("estimated-resolution-date-request", kwargs={"barrier_id": barrier.id})

        response = self.api_client.get(url, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {}
