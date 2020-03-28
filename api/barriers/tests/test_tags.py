from django.urls import reverse
from rest_framework import status

from barriers.tests.factories import BarrierFactory, BarrierTagFactory
from core.test_utils import APITestMixin


class TestReportDetail(APITestMixin):
    def test_get_barrier_tags(self):
        barrier = BarrierFactory()
        brexit_tag = BarrierTagFactory(title="brexit")
        barrier.tags.add(brexit_tag)

        url = reverse("get-barrier", kwargs={"pk": barrier.id})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


