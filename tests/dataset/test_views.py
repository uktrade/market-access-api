from datetime import datetime

import time_machine
import freezegun
from django.contrib.auth.models import Permission
from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin, create_test_user
from api.feedback.models import Feedback
from api.metadata.constants import (
    FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS,
    FEEDBACK_FORM_SATISFACTION_ANSWERS,
)
from api.metadata.models import BarrierTag, Organisation
from tests.barriers.factories import BarrierFactory

freezegun.configure(extend_ignore_list=["transformers"])


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

    @freezegun.freeze_time("2020-01-25")
    def test_list_barriers(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        adv_engineering = "af959812-6095-e211-a939-e4115bead28a"
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        db_barrier = BarrierFactory(
            created_by=user,
            country=spain,
            sectors=(adv_engineering,),
            status=2,
            status_date=datetime(2020, 1, 1, tzinfo=UTC),
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
        assert barrier["status"]["name"] == "Open"
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
                "status": {"id": 2, "name": "Open"},
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
        org2 = Organisation.objects.get(id=2)
        barrier = BarrierFactory()
        barrier.organisations.add(org1)
        barrier.organisations.add(org2)

        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        data_item = response.data["results"][0]
        assert "government_organisations" in data_item.keys()

        assert org1.name == data_item["government_organisations"][0]
        assert org2.name == data_item["government_organisations"][1]

    def test_is_regional_trade_plan_field(self):
        barrier = BarrierFactory(archived=False)

        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        data_item = response.data["results"][0]
        assert len(response.data["results"]) == 1
        assert data_item["is_regional_trade_plan"] is False

        tag = BarrierTag.objects.get(title="Regional Trade Plan")
        barrier.tags.add(tag)

        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        data_item = response.data["results"][0]
        assert len(response.data["results"]) == 1
        assert data_item["is_regional_trade_plan"] is True

    def test_null_main_sector_all_sector(self):
        """Tests that when main_sector is null and all_sectors is true, the main_sector is set to 'all sectors'"""
        barrier = BarrierFactory(main_sector=None, all_sectors=True)
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        barrier_data = response.data["results"][0]
        assert barrier_data["id"] == str(barrier.id)

        assert barrier_data["main_sector"] == "All sectors"

    def test_main_sector(self):
        """Tests that when main_sector is set, the main_sector returned is the name of the sector"""
        barrier = BarrierFactory(
            main_sector="af959812-6095-e211-a939-e4115bead28a", all_sectors=True
        )
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        barrier_data = response.data["results"][0]
        assert barrier_data["id"] == str(barrier.id)

        assert barrier_data["main_sector"] == "Advanced engineering"


class TestFeedbackDataset(APITestMixin):
    def test_no_feedback(self):
        url = reverse("dataset:feedback-list")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_feedback(self):
        feedback1 = Feedback.objects.create(
            satisfaction=FEEDBACK_FORM_SATISFACTION_ANSWERS.VERY_SATISFIED,
            attempted_actions=[FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.PROGRESS_UPDATE],
            feedback_text="This feedback is very good",
        )
        feedback2 = Feedback.objects.create(
            satisfaction=FEEDBACK_FORM_SATISFACTION_ANSWERS.DISSATISFIED,
            attempted_actions=[FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.PROGRESS_UPDATE],
            feedback_text="This feedback is ",
        )
        url = reverse("dataset:feedback-list")
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == len(response.data["results"])
        assert feedback1.satisfaction == response.data["results"][0]["satisfaction"]
        assert feedback2.satisfaction == response.data["results"][1]["satisfaction"]
        assert (
            feedback1.attempted_actions
            == response.data["results"][0]["attempted_actions"]
        )
        assert (
            feedback2.attempted_actions
            == response.data["results"][1]["attempted_actions"]
        )
        assert feedback1.feedback_text == response.data["results"][0]["feedback_text"]
        assert feedback2.feedback_text == response.data["results"][1]["feedback_text"]


class TestUserActivityLogDataset(APITestMixin):
    def test_no_logs(self):
        url = reverse("dataset:user-activity-log")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    @time_machine.travel("2022-10-15 12:00:01")
    def test_logs(self):
        # perform user login
        assert datetime.now() == datetime(2022, 10, 15, 12, 0, 1)
        csv_downd_permission_codename = "download_barriers"
        permission = Permission.objects.get(codename=csv_downd_permission_codename)
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        user.is_superuser = True
        user.is_enabled = True
        user.save()
        self.create_api_client(user=user)

        url = reverse("dataset:user-activity-log")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

        # user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        # client = Client()
        self.api_client.force_login(user)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        csv_download_url = reverse("barriers-s3-email")

        response = self.api_client.get(csv_download_url)
        assert response.status_code == status.HTTP_200_OK

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
