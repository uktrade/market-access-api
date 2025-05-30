import json

from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from api.metadata.models import PolicyTeam
from api.metadata.serializers import PolicyTeamSerializer


class TestMetadata(APITestMixin):
    def test_metadata_dict(self):
        """Test all items are exposed using metadata"""
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert bool(response.json()) is True

    def test_barrier_terms(self):
        expected = {
            "1": "A procedural, short-term barrier",
            "2": "A long-term strategic barrier",
        }
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_terms"] is not None
        assert json.dumps(response.data["barrier_terms"]) == json.dumps(expected)

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

    def test_policy_teams(self):

        url = reverse("metadata")

        response = self.api_client.get(url)

        assert PolicyTeam.objects.count() == 18
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["policy_teams"]) == 18
        assert (
            response.data["policy_teams"]
            == PolicyTeamSerializer(PolicyTeam.objects.all(), many=True).data
        )

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

    def test_trade_direction(self):
        key = "trade_direction"
        expected = {
            "1": "Exporting from the UK or investing overseas",
            "2": "Importing or investing into the UK",
        }

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert response.data[key] is not None
        assert expected == response.data[key]

    def test_government_organisations(self):
        key = "government_organisations"

        url = reverse("metadata")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert response.data[key] is not None
        assert 54 == len(response.data[key])

        org = response.data[key][0]
        assert "id" in org.keys()
        assert "name" in org.keys()
        assert "organisation_type" in org.keys()

    def test_top_priority_status(self):
        key = "top_priority_status"
        expected = {
            "NONE": "",
            "APPROVAL_PENDING": "Top 100 Approval Pending",
            "REMOVAL_PENDING": "Top 100 Removal Pending",
            "APPROVED": "Top 100 Priority",
            "RESOLVED": "Top 100 Priority Resolved",
        }

        url = reverse("metadata")
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert response.data[key] is not None
        assert expected == response.data[key]

    def test_barrier_tags(self):
        expected = [
            "Scoping (Top 100 priority barrier)",
            "COVID-19",
            "Programme Fund",
            "International Standards",
            "Clean Growth",
            "Regional Trade Plan",
            "EU Market Access Board",
            "Wales Priority",
            "Europe Priority",
            "Programme Fund - Facilitative Regional",
            "Programme Fund - Regulator",
            "Market Distorting Practices (MDP)",
            "Market Shaping",
        ]
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_tags"] is not None

        tag_titles = [tag["title"] for tag in response.data["barrier_tags"]]
        assert json.dumps(tag_titles) == json.dumps(expected)

    def test_search_ordering_choices(self):
        expected = [
            ("-reported", "Date reported (newest)"),
            ("reported", "Date reported (oldest)"),
            ("-updated", "Last updated (most recent)"),
            ("updated", "Last updated (least recent)"),
            ("-value", "Value (highest)"),
            ("value", "Value (lowest)"),
            ("-resolution", "Estimated resolution date (most recent)"),
            ("resolution", "Estimated resolution date (least recent)"),
            ("-resolved", "Date resolved (most recent)"),
            ("resolved", "Date resolved (least recent)"),
            ("relevance", "Relevence to the search term"),
        ]
        url = reverse("metadata")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["search_ordering_choices"] is not None
        assert json.dumps(response.data["search_ordering_choices"]) == json.dumps(
            expected
        )
