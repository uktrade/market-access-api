from datetime import datetime

from freezegun import freeze_time
from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.models import Organisation
from tests.barriers.factories import BarrierFactory


class TestBarriersDataset(APITestMixin):

    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_list_barriers_count(self):
        count = 2
        BarrierFactory.create_batch(count)

        assert count == Barrier.objects.count()

        dataset_url = reverse("dataset:barrier-list")
        response = self.api_client.get(dataset_url)
        assert status.HTTP_200_OK == response.status_code
        assert count == len(response.data["results"])

    @freeze_time("2020-01-25")
    def test_list_barriers(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        adv_engineering = "af959812-6095-e211-a939-e4115bead28a"
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        db_barrier = BarrierFactory(
            created_by=user,
            country=spain,
            sectors=(adv_engineering,),
            status=2, status_date=datetime(2020, 1, 1, tzinfo=UTC),
        )
        TeamMember.objects.create(barrier=db_barrier, user=user, role="Wobble")

        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        barrier = response.data["results"][0]
        assert barrier["id"] == str(db_barrier.id)
        assert barrier["code"] is not None
        assert barrier["title"] is not None
        assert barrier["status"]["name"] == "Open: In progress"
        assert barrier["priority"]["name"] == "Unknown"
        assert barrier["country"]["name"] == "Spain"
        assert barrier["country"]["overseas_region"]["name"] == "Europe"
        assert barrier["admin_areas"] == []
        assert barrier["sectors"][0]["name"] == "Advanced engineering"
        assert barrier["product"] is not None
        assert barrier["term"] is not None
        assert barrier["categories"] == []
        assert barrier["source"]["name"] == "Company"
        assert barrier["team_count"] == 1
        assert barrier["status_date"] == "2020-01-01"
        assert barrier["economic_assessments"] == []
        assert barrier["status_history"] == [
            {
                "date": "2020-01-25T00:00:00+00:00",
                "status": {"id": 2, "name": "Open: In progress"},
            }
        ]

    def test_eu_barrier_overseas_region(self):
        barrier = BarrierFactory(trading_bloc="TB00016", country=None)
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        barrier_data = response.data["results"][0]
        assert barrier_data["id"] == str(barrier.id)

        overseas_regions = barrier_data["trading_bloc"]["overseas_regions"]
        assert len(overseas_regions) == 1
        assert overseas_regions[0]["name"] == "Europe"

    def test_government_organisations(self):
        org1 = Organisation.objects.get(id=1)
        barrier = BarrierFactory()
        barrier.organisations.add(org1)

        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        data_item = response.data["results"][0]
        assert "government_organisations" in data_item.keys()
        assert org1.id == data_item["government_organisations"][0]["id"]
