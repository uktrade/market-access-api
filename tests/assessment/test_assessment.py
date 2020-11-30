from http import HTTPStatus
import pytest

from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory

pytestmark = [
    pytest.mark.django_db
]


class TestAssessment(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_add_commercial_value(self, barrier):
        url = reverse("get-barrier", kwargs={"pk": barrier.id})

        response = self.api_client.patch(
            url,
            format="json",
            data={"commercial_value": 1500000}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["commercial_value"] == 1500000

    def test_add_commercial_value_explanation(self, barrier):
        url = reverse("get-barrier", kwargs={"pk": barrier.id})
        expected_explanation = "Wibble wobble"

        response = self.api_client.patch(
            url,
            format="json",
            data={"commercial_value_explanation": expected_explanation}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.data["commercial_value_explanation"] == expected_explanation
