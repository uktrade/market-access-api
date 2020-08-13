from datetime import datetime
from freezegun import freeze_time
from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import BarrierInstance
from api.core.test_utils import APITestMixin, create_test_user
from api.collaboration.models import TeamMember

from tests.barriers.factories import BarrierFactory


class TestBarriersDataset(APITestMixin):

    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("dataset:barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_list_barriers_dataset_attributes(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        adv_engineering = "af959812-6095-e211-a939-e4115bead28a"
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        db_barrier = BarrierFactory(
            created_by=user,
            export_country=spain,
            sectors=(adv_engineering,),
            status=2, status_date=datetime(2020, 1, 1, tzinfo=UTC),
        )
        TeamMember.objects.create(barrier=db_barrier, user=user, role="Wobble")

        url = reverse("dataset:barriers")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        barrier = response.data["results"][0]
        assert barrier["id"] == str(db_barrier.id)
        assert barrier["code"] is not None
        assert barrier["barrier_title"] is not None
        assert barrier["status"] == "Open: In progress"
        assert barrier["priority"] == "Unknown"
        assert barrier["country"] == ["Spain"]
        assert barrier["overseas_region"] == "Europe"
        assert barrier["admin_areas"] == []
        assert barrier["sectors"] == ["Advanced Engineering"]
        assert barrier["product"] is not None
        assert barrier["scope"] is not None
        assert barrier["categories"] == []
        assert barrier["source"] == "Company"
        assert barrier["team_count"] == 1
        assert barrier["status_date"] == "2020-01-01"
        assert barrier["assessment_impact"] is None
        assert barrier["value_to_economy"] is None
        assert barrier["import_market_size"] is None
        assert barrier["commercial_value"] is None
        assert barrier["commercial_value_explanation"] is None
        assert barrier["export_value"] is None

    def test_list_barriers_dataset(self):
        count = 2
        BarrierFactory.create_batch(count)

        assert count == BarrierInstance.objects.count()

        dataset_url = reverse("dataset:barriers")
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
            export_country=spain,
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
        assert barrier["sectors"][0]["name"] == "Advanced Engineering"
        assert barrier["product"] is not None
        assert barrier["term"] is not None
        assert barrier["categories"] == []
        assert barrier["source"]["name"] == "Company"
        assert barrier["team_count"] == 1
        assert barrier["status_date"] == "2020-01-01"
        assert barrier["assessment"] is None
        assert barrier["status_history"] == [
            {
                "date": "2020-01-25T00:00:00+00:00",
                "status": {"id": 2, "name": "Open: In progress"},
            }
        ]
