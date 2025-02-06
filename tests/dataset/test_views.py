from datetime import datetime

import freezegun
import time_machine
from django.contrib.auth import get_user_model
from mock import PropertyMock, patch
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
    PublicBarrierStatus,
)
from api.metadata.models import BarrierTag, Organisation
from tests.barriers.factories import BarrierFactory

freezegun.configure(extend_ignore_list=["transformers"])
User = get_user_model()


class TestBarriersDataset(APITestMixin):
    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_list_barriers_count(self, mock_public_barrier_status):
        count = 2
        BarrierFactory.create_batch(count)
        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN

        assert count == Barrier.objects.count()

        dataset_url = reverse("dataset:barrier-list")
        response = self.api_client.get(dataset_url)
        assert status.HTTP_200_OK == response.status_code
        assert count == len(response.data["results"])

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_list_barriers(self, mock_public_barrier_status):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        adv_engineering = "af959812-6095-e211-a939-e4115bead28a"
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        ts = datetime.now()
        with freezegun.freeze_time(ts):
            db_barrier = BarrierFactory(
                created_by=user,
                country=spain,
                sectors=(adv_engineering,),
                status=2,
                status_date=datetime(2020, 1, 1, tzinfo=UTC),
            )
            TeamMember.objects.create(barrier=db_barrier, user=user, role="Wobble")
        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN

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
        assert barrier["source"]["name"] == "Company"
        assert barrier["team_count"] == 1
        assert barrier["status_date"] == "2020-01-01"
        assert barrier["economic_assessments"] == []
        assert barrier["status_history"] == [
            {
                "date": barrier["status_history"][0]["date"],
                "status": {"id": 2, "name": "Open"},
            }
        ]

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_eu_barrier_overseas_region(self, mock_public_barrier_status):
        barrier = BarrierFactory(trading_bloc="TB00016", country=None)
        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        barrier_data = response.data["results"][0]
        assert barrier_data["id"] == str(barrier.id)

        overseas_regions = barrier_data["trading_bloc"]["overseas_regions"]
        assert len(overseas_regions) == 1
        assert overseas_regions[0]["name"] == "Europe"

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_government_organisations(self, mock_public_barrier_status):
        org1 = Organisation.objects.get(id=1)
        org2 = Organisation.objects.get(id=2)
        barrier = BarrierFactory()
        barrier.organisations.add(org1)
        barrier.organisations.add(org2)

        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN

        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        data_item = response.data["results"][0]
        assert "government_organisations" in data_item.keys()

        assert org1.name == data_item["government_organisations"][0]
        assert org2.name == data_item["government_organisations"][1]

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_is_regional_trade_plan_field(self, mock_public_barrier_status):
        barrier = BarrierFactory(archived=False)
        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN

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

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_null_main_sector_all_sector(self, mock_public_barrier_status):
        """Tests that when main_sector is null and all_sectors is true, the main_sector is set to 'all sectors'"""
        barrier = BarrierFactory(main_sector=None, all_sectors=True)
        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN
        url = reverse("dataset:barrier-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        barrier_data = response.data["results"][0]
        assert barrier_data["id"] == str(barrier.id)

        assert barrier_data["main_sector"] == "All sectors"

    @patch(
        "api.barriers.models.PublicBarrier.public_view_status",
        new_callable=PropertyMock,
    )
    def test_main_sector(self, mock_public_barrier_status):
        """Tests that when main_sector is set, the main_sector returned is the name of the sector"""
        barrier = BarrierFactory(
            main_sector="af959812-6095-e211-a939-e4115bead28a", all_sectors=True
        )
        mock_public_barrier_status.return_value = PublicBarrierStatus.UNKNOWN
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
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        user.is_superuser = True
        user.is_enabled = True
        user.save()
        self.create_api_client(user=user)

        url = reverse("dataset:user-activity-log")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

        self.api_client.force_login(user)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        csv_download_url = reverse("barrier-downloads")
        BarrierFactory()

        response = self.api_client.post(csv_download_url)
        assert response.status_code == status.HTTP_201_CREATED

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2


class TestUserDataset(APITestMixin):
    def test_base_user(self):
        url = reverse("dataset:user-list")
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        user = User.objects.first()
        ts1 = datetime(2024, 9, 1, 0, 0, 0)
        with freezegun.freeze_time(ts1):
            self.api_client.force_login(user)

        response = self.api_client.get(url)

        assert response.data["results"][0]["last_login"] == ts1.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    def test_user_added(self):
        create_test_user()
        url = reverse("dataset:user-list")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert len(response.data["results"]) == 2
