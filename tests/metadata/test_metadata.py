import json

from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user


class TestCategories(APITestMixin):
    def test_metadata_dict(self):
        """Test all items are exposed using metadata"""
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert bool(response.json()) is True

    def test_status_types(self):
        expected = {
            "1": "A problem that is blocking a specific export or investment",
            "2": "A strategic barrier likely to affect multiple exports or sectors",
        }
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status_types"] is not None
        assert json.dumps(response.data["status_types"]) == json.dumps(expected)

    def test_loss_range(self):
        expected = {
            "1": "Less than £1m",
            "2": "£1m to £10m",
            "3": "£10m to £100m",
            "4": "Over £100m",
        }
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["loss_range"] is not None
        assert json.dumps(response.data["loss_range"]) == json.dumps(expected)

    def test_stage_status(self):
        expected = {"1": "NOT STARTED", "2": "IN PROGRESS", "3": "COMPLETED"}
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["stage_status"] is not None
        assert json.dumps(response.data["stage_status"]) == json.dumps(expected)

    def test_govt_response(self):
        expected = {
            "1": "None, this is for our information only at this stage",
            "2": "In-country support from post",
            "3": "Broader UK government sensitivities",
        }

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["govt_response"] is not None
        assert json.dumps(response.data["govt_response"]) == json.dumps(expected)

    def test_publish_response(self):
        expected = {"1": "Yes", "2": "No", "3": "Don't publish without consultation"}

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["publish_response"] is not None
        assert json.dumps(response.data["publish_response"]) == json.dumps(expected)

    def test_report_status(self):
        expected = {
            "0": "Unfinished",
            "1": "AwaitingScreening",
            "2": "Accepted",
            "3": "Rejected",
            "4": "Archived",
        }

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["report_status"] is not None
        assert json.dumps(response.data["report_status"]) == json.dumps(expected)

    def test_report_stages(self):
        expected = {
            "1.0": "Add a barrier",
            "1.1": "Barrier status",
            "1.2": "Location of the barrier",
            "1.3": "Sectors affected by the barrier",
            "1.4": "About the barrier",
            "1.5": "Barrier summary",
        }

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["report_stages"] is not None
        assert json.dumps(response.data["report_stages"]) == json.dumps(expected)

    def test_support_type(self):
        expected = {
            "1": "Market access team to provide support on next steps",
            "2": "None, I’m going to handle next steps myself as the lead coordinator",
        }

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["support_type"] is not None
        assert json.dumps(response.data["support_type"]) == json.dumps(expected)

    def test_countries(self):
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["countries"] is not None
        assert bool(response.data["countries"]) is True
