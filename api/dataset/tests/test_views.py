import datetime

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import BarrierInstance
from api.barriers.tests.test_utils import add_multiple_barriers
from api.core.test_utils import APITestMixin


class TestBarriersDataset(APITestMixin):
    @pytest.fixture
    def setup_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "a05f66a0-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        return instance.id

    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("dataset-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_one_report(self, setup_barrier):
        instance_id = setup_barrier
        url = reverse("dataset-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        barrier = response.data["results"][0]
        assert barrier["id"] == str(instance_id)
        assert barrier["code"] is not None
        assert barrier["barrier_title"] == "Some title"
        assert barrier["status"] == "Resolved: In full"
        assert barrier["priority"] == "Unknown"
        assert barrier["country"] == ["Austria"]
        assert barrier["overseas_region"] == "Europe"
        assert barrier["admin_areas"] == []
        assert barrier["sectors"] == ['Advanced Engineering', 'Aerospace']
        assert barrier["product"] == "Some product"
        assert barrier["scope"] == "A strategic barrier likely to affect multiple exports or sectors"
        assert barrier["categories"] == []
        assert barrier["source"] == "Other"
        assert barrier["team_count"] == 1
        assert barrier["resolved_date"] == datetime.date(2018, 9, 10)
        assert barrier["assessment_impact"] is None
        assert barrier["value_to_economy"] is None
        assert barrier["import_market_size"] is None
        assert barrier["commercial_value"] is None
        assert barrier["export_value"] is None

    def test_list_barriers_get_multiple_barriers_country_filter(self):
        client = self.api_client
        count = 10
        add_multiple_barriers(count, client)
        list_url = reverse("list-barriers")
        response = self.api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        dataset_url = reverse("dataset-barriers")
        response = self.api_client.get(dataset_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == count
