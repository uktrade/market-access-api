from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


class TestPreliminaryAssessments(APITestMixin):
    @pytest.fixture
    def barrier(self):
        return BarrierFactory()

    def test_preliminary_assessment_not_found(self, barrier):
        url = reverse("preliminary-assessment", kwargs={"barrier_id": barrier.id})
        response = self.api_client.get(url, format="json")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_preliminary_assessment_bad_request(self):
        import uuid

        url = reverse(
            "preliminary-assessment", kwargs={"barrier_id": str(uuid.uuid4())}
        )
        response = self.api_client.get(url, format="json")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_preliminary_assessment_post_and_get_success(self, barrier):
        data = {"value": 1, "details": "asdasd"}
        url = reverse("preliminary-assessment", kwargs={"barrier_id": barrier.id})
        response = self.api_client.post(url, format="json", data=data)

        assert response.status_code == HTTPStatus.CREATED

        response = self.api_client.get(url, format="json")

        assert response.status_code == HTTPStatus.OK
        assert response.data == {**data, **{"barrier_id": str(barrier.id)}}

    def test_preliminary_assessment_post_and_patch_success(self, barrier):
        data = {"value": 1, "details": "asdasd"}
        url = reverse("preliminary-assessment", kwargs={"barrier_id": barrier.id})
        response = self.api_client.post(url, format="json", data=data)

        assert response.status_code == HTTPStatus.CREATED

        response = self.api_client.patch(
            url, format="json", data={"details": "new_details"}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.data["details"] == "new_details"
