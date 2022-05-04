import datetime
from datetime import date

import django.db.models
import pytest
from django.test import TestCase
from rest_framework.test import APITestCase

from api.action_plans.models import ActionPlan
from api.barriers.models import BarrierProgressUpdate
from api.barriers.serializers.data_workspace import DataWorkspaceSerializer
from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.constants import PROGRESS_UPDATE_CHOICES
from tests.action_plans.factories import (
    ActionPlanMilestoneFactory,
    ActionPlanTaskFactory,
)
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import BarrierTagFactory

pytestmark = [pytest.mark.django_db]


class TestDataWarehouseExport(TestCase):
    def test_datawarehouse_action_plans_values(self):

        owner = create_test_user()

        barrier = BarrierFactory(status_date=date.today())
        ActionPlan.objects.filter(barrier=barrier).update(
            barrier=barrier,
            owner=owner,
            current_status="Progress update here",
            current_status_last_updated=date(2021, 8, 1),
            strategic_context="Strategic context text",
            strategic_context_last_updated=date(2021, 7, 1),
        )
        action_plan = barrier.action_plan
        barrier.refresh_from_db()

        data_with_empty_action_plan = DataWorkspaceSerializer(barrier).data
        assert data_with_empty_action_plan["action_plan_added"] is False
        assert (
            data_with_empty_action_plan["action_plan"]["progress_update"]
            == "Progress update here"
        )
        assert (
            data_with_empty_action_plan["action_plan"]["progress_update_updated_on"]
            == "2021-08-01"
        )
        assert (
            data_with_empty_action_plan["action_plan"]["strategic_context"]
            == "Strategic context text"
        )
        assert (
            data_with_empty_action_plan["action_plan"]["strategic_context_updated_on"]
            == "2021-07-01"
        )

        milestone1 = ActionPlanMilestoneFactory(action_plan=action_plan)
        milestone2 = ActionPlanMilestoneFactory(action_plan=action_plan)
        task1 = ActionPlanTaskFactory(
            milestone=milestone1,
            action_type="SCOPING_AND_RESEARCH",
            action_type_category="Dialogue",
            status="IN_PROGRESS",
        )
        task2 = ActionPlanTaskFactory(
            milestone=milestone1,
            action_type="LOBBYING",
            action_type_category="Lobbying by officials",
            status="IN_PROGRESS",
        )
        task3 = ActionPlanTaskFactory(
            milestone=milestone2,
            action_type="BILATERAL_ENGAGEMENT",
            action_type_category="Creating and maintaining trade agreements",
            status="IN_PROGRESS",
        )
        task4 = ActionPlanTaskFactory(
            milestone=milestone2,
            action_type="WHITEHALL_FUNDING_STREAMS",
            action_type_category="Prosperity fund",
            status="IN_PROGRESS",
        )

        data_with_action_plan = DataWorkspaceSerializer(barrier).data
        assert data_with_action_plan["action_plan_added"] is True
        assert (
            data_with_action_plan["action_plan"]["action_plan_percent_complete"]
            == "0.0%"
        )
        assert data_with_action_plan["action_plan"]["action_plan_owner"] == owner.email
        assert data_with_action_plan["action_plan"]["all_intervention_types"] == (
            "Dialogue - Scoping/Research,Lobbying by "
            "officials - Lobbying,Creating and maintaining "
            "trade agreements - Bilateral "
            "engagement,Prosperity fund - Whitehall funding "
            "streams"
        )
        assert data_with_action_plan["action_plan"]["number_of_objectives"] == 2
        assert (
            data_with_action_plan["action_plan"]["number_of_objectives_complete"] == 0
        )
        assert data_with_action_plan["action_plan"]["number_of_interventions"] == 4
        assert (
            data_with_action_plan["action_plan"]["number_of_interventions_complete"]
            == 0
        )

        task4.status = "COMPLETED"
        task4.save()

        data_with_action_plan = DataWorkspaceSerializer(barrier).data
        assert data_with_action_plan["action_plan"]["number_of_objectives"] == 2
        assert (
            data_with_action_plan["action_plan"]["number_of_objectives_complete"] == 0
        )
        assert data_with_action_plan["action_plan"]["number_of_interventions"] == 4
        assert (
            data_with_action_plan["action_plan"]["number_of_interventions_complete"]
            == 1
        )
        assert (
            data_with_action_plan["action_plan"]["action_plan_percent_complete"]
            == "25.0%"
        )

        task3.status = "COMPLETED"
        task3.save()

        data_with_action_plan = DataWorkspaceSerializer(barrier).data
        assert data_with_action_plan["action_plan"]["number_of_objectives"] == 2
        assert (
            data_with_action_plan["action_plan"]["number_of_objectives_complete"] == 1
        )
        assert data_with_action_plan["action_plan"]["number_of_interventions"] == 4
        assert (
            data_with_action_plan["action_plan"]["number_of_interventions_complete"]
            == 2
        )
        assert (
            data_with_action_plan["action_plan"]["action_plan_percent_complete"]
            == "50.0%"
        )

        task1.status = "COMPLETED"
        task1.save()
        task2.status = "COMPLETED"
        task2.save()

        data_with_action_plan = DataWorkspaceSerializer(barrier).data
        assert data_with_action_plan["action_plan"]["number_of_objectives"] == 2
        assert (
            data_with_action_plan["action_plan"]["number_of_objectives_complete"] == 2
        )
        assert data_with_action_plan["action_plan"]["number_of_interventions"] == 4
        assert (
            data_with_action_plan["action_plan"]["number_of_interventions_complete"]
            == 4
        )
        assert (
            data_with_action_plan["action_plan"]["action_plan_percent_complete"]
            == "100.0%"
        )

    def test_has_value_for_is_top_priority(self):
        barrier = BarrierFactory(status_date=date.today())
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert "is_top_priority" in serialised_data.keys()

    def test_value_for_is_top_priority_is_bool(self):
        barrier = BarrierFactory(status_date=date.today())
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert "is_top_priority" in serialised_data.keys() and isinstance(
            serialised_data["is_top_priority"], bool
        )

    def test_data_warehouse_is_top_priority_barrier(self):
        tag_title = "Very Important Thing"
        tag = BarrierTagFactory(title=tag_title, is_top_priority_tag=True)
        barrier = BarrierFactory(tags=(tag,), status_date=date.today())
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert (
            "is_top_priority" in serialised_data.keys()
            and serialised_data["is_top_priority"] is True
        )

    def test_data_warehouse_is_not_top_priority_barrier(self):
        tag_title = "Very Important Thing"
        tag = BarrierTagFactory(title=tag_title, is_top_priority_tag=False)
        barrier = BarrierFactory(tags=(tag,), status_date=date.today())
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert (
            "is_top_priority" in serialised_data.keys()
            and serialised_data["is_top_priority"] is False
        )


class TestBarrierDataWarehouseDeliveryConfidenceSerializer(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        # self.user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        self.barrier = BarrierFactory(status_date=date.today())

    def test_latest_progress_update_in_data(self):
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            created_by=self.user,
        )
        self.barrier.progress_updates.add(progress_update)
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        assert "latest_progress_update" in serialised_data

    def test_latest_progress_update_status_in_data(self):
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            created_by=self.user,
        )
        self.barrier.progress_updates.add(progress_update)
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        assert "status" in serialised_data["latest_progress_update"]

    def test_latest_progress_update_status_is_null_when_no_progress_updates(self):
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        assert (
            "latest_progress_update" in serialised_data
            and serialised_data["latest_progress_update"] is None
        )

    def test_latest_progress_update_status_on_track_is_readable(self):
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            created_by=self.user,
        )
        self.barrier.progress_updates.add(progress_update)
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        assert (
            "status" in serialised_data["latest_progress_update"]
            and serialised_data["latest_progress_update"]["status"]
            == PROGRESS_UPDATE_CHOICES["ON_TRACK"]
        )

    def test_latest_progress_update_status_risk_of_delay_is_readable(self):
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.RISK_OF_DELAY,
            created_by=self.user,
        )
        self.barrier.progress_updates.add(progress_update)
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        assert (
            "status" in serialised_data["latest_progress_update"]
            and serialised_data["latest_progress_update"]["status"]
            == PROGRESS_UPDATE_CHOICES["RISK_OF_DELAY"]
        )

    def test_latest_progress_update_status_delayed_is_readable(self):
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.DELAYED,
            created_by=self.user,
        )
        self.barrier.progress_updates.add(progress_update)
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        assert (
            "status" in serialised_data["latest_progress_update"]
            and serialised_data["latest_progress_update"]["status"]
            == PROGRESS_UPDATE_CHOICES["DELAYED"]
        )

    def test_user_fields_are_serialised(self):
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            created_by=self.user,
            created_on=datetime.datetime.now(),
            modified_by=self.user,
            modified_on=datetime.datetime.now(),
            archived_by=self.user,
            archived_on=datetime.datetime.now(),
            unarchived_by=self.user,
            unarchived_on=datetime.datetime.now(),
        )
        self.barrier.progress_updates.add(progress_update)
        serialised_data = DataWorkspaceSerializer(self.barrier).data
        latest_progress_update = serialised_data["latest_progress_update"]
        assert not isinstance(
            latest_progress_update["created_by"], django.db.models.Model
        )
        assert not isinstance(
            latest_progress_update["modified_by"], django.db.models.Model
        )
        assert not isinstance(
            latest_progress_update["archived_by"], django.db.models.Model
        )
        assert not isinstance(
            latest_progress_update["unarchived_by"], django.db.models.Model
        )
