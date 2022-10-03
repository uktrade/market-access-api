from http import HTTPStatus
from unittest.mock import patch

import pytest
from notifications_python_client.notifications import NotificationsAPIClient
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


class TestAssessment(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_add_commercial_value(self, barrier):
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            url = reverse("get-barrier", kwargs={"pk": barrier.id})

            response = self.api_client.patch(
                url, format="json", data={"commercial_value": 1500000}
            )
            assert response.status_code == HTTPStatus.OK
            assert response.data["commercial_value"] == 1500000

    def test_add_commercial_value_explanation(self, barrier):
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            url = reverse("get-barrier", kwargs={"pk": barrier.id})
            expected_explanation = "Wibble wobble"

            response = self.api_client.patch(
                url,
                format="json",
                data={"commercial_value_explanation": expected_explanation},
            )
            assert response.status_code == HTTPStatus.OK
            assert response.data["commercial_value_explanation"] == expected_explanation
