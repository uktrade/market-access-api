from rest_framework.test import APITestCase

from api.healthcheck.models import HealthCheck


class TestViews(APITestCase):
    """
    Test Healthcheck views
    """

    def test_check_view(self):
        response = self.client.get("/check/")
        assert 200 == response.status_code
        assert "OK" == response.data["status"]
        assert response.data["duration"] > 0
        assert response.data["duration"] < 1

    def test_check_view_no_data_fail(self):
        HealthCheck.objects.all().delete()
        response = self.client.get("/check/")
        assert 200 == response.status_code
        assert "FAIL" == response.data["status"]
        assert response.data["duration"] > 0
        assert response.data["duration"] < 1
