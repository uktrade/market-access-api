from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from ..models import BarrierInteraction
from .test_utils import TestUtils


class TestListInteractions(APITestMixin):
    def _test_no_interactions(self):
        """Test there are no barrier interactions using list"""
        url = reverse("list-interactions", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def _test_list_reports_get_one_report(self):
        BarrierInstance(problem_status=1).save()
        url = reverse("list-interactions")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
