import datetime
from datetime import date

import django.db.models
import freezegun
import pytest
from django.test import TestCase
from rest_framework.test import APITestCase

from api.action_plans.models import ActionPlan
from api.barriers.models import BarrierProgressUpdate
from api.barriers.serializers.data_workspace import DataWorkspaceSerializer
from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS,
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC,
    PRIORITY_LEVELS,
    PROGRESS_UPDATE_CHOICES,
    TOP_PRIORITY_BARRIER_STATUS,
    BarrierStatus,
)
from api.metadata.models import BarrierTag
from tests.action_plans.factories import (
    ActionPlanMilestoneFactory,
    ActionPlanTaskFactory,
)
from tests.assessment.factories import EconomicImpactAssessmentFactory
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


freezegun.configure(extend_ignore_list=["transformers"])


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
        assert data_with_empty_action_plan["action_plan_added"] is True
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

    def test_has_value_for_is_resolved_top_priority(self):
        barrier = BarrierFactory(status_date=date.today())
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert "is_resolved_top_priority" in serialised_data.keys()

    def test_value_for_is_resolved_top_priority_is_bool(self):
        barrier = BarrierFactory(status_date=date.today())
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert isinstance(serialised_data["is_resolved_top_priority"], bool)

    def test_is_resolved_top_priority_value_for_resolved_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.RESOLVED,
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is True

    def test_is_resolved_top_priority_value_for_approved_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED,
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_approval_pending_top_priority_is_correct(
        self,
    ):
        barrier = BarrierFactory(
            status_date=date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING,
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_removal_pending_top_priority_is_correct(
        self,
    ):
        barrier = BarrierFactory(
            status_date=date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_is_resolved_top_priority_value_for_no_top_priority_is_correct(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.NONE,
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert serialised_data["is_resolved_top_priority"] is False

    def test_data_warehouse_is_top_priority_barrier(self):

        # Left: top_priority_status - Right: expected is_top_priority value
        top_priority_status_to_is_top_priority_map = {
            TOP_PRIORITY_BARRIER_STATUS.APPROVED: True,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING: True,
            TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING: False,
            TOP_PRIORITY_BARRIER_STATUS.NONE: False,
        }

        priority_summary = "PB100 status summary"

        barrier = BarrierFactory(status_date=date.today())

        for (
            top_priority_status,
            is_top_priority,
        ) in top_priority_status_to_is_top_priority_map.items():
            barrier.top_priority_status = top_priority_status
            expected_priority_summary = priority_summary if is_top_priority else ""
            barrier.priority_summary = expected_priority_summary

            serialised_data = DataWorkspaceSerializer(barrier).data
            assert serialised_data["top_priority_status"] == top_priority_status
            assert (
                "is_top_priority" in serialised_data.keys()
                and serialised_data["is_top_priority"] is is_top_priority
            )
            assert (
                "priority_summary" in serialised_data
                and serialised_data["priority_summary"] == expected_priority_summary
            )

    def test_resolved_date_empty_for_non_resolved_barriers(self):
        barrier_open_pending = BarrierFactory(status_date=date.today(), status=1)
        barrier_open_in_progress = BarrierFactory(status_date=date.today(), status=2)
        barrier_dormant = BarrierFactory(status_date=date.today(), status=5)
        barrier_archived = BarrierFactory(status_date=date.today(), status=6)
        barrier_unknown = BarrierFactory(status_date=date.today(), status=7)

        test_barriers = [
            barrier_open_pending,
            barrier_open_in_progress,
            barrier_dormant,
            barrier_archived,
            barrier_unknown,
        ]

        for barrier in test_barriers:
            serialised_data = DataWorkspaceSerializer(barrier).data
            assert "resolved_date" in serialised_data.keys()
            assert serialised_data["resolved_date"] is None

    def test_resolved_date_populated_for_resolved_barriers(self):
        date_today = date.today()
        barrier_resolved_part = BarrierFactory(status_date=date_today, status=3)
        barrier_resolved_full = BarrierFactory(status_date=date_today, status=4)
        for barrier in [barrier_resolved_part, barrier_resolved_full]:
            serialised_data = DataWorkspaceSerializer(barrier).data
            assert "resolved_date" in serialised_data.keys()
            assert serialised_data["resolved_date"] == date_today

    def test_valuation_assessment_midpoint(self):
        date_today = date.today()
        barrier = BarrierFactory(
            status_date=date_today, status=BarrierStatus.OPEN_IN_PROGRESS
        )
        impact_level = 6
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        serialised_data = DataWorkspaceSerializer(barrier).data

        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]
        assert "valuation_assessment_midpoint" in serialised_data.keys()
        assert (
            serialised_data["valuation_assessment_midpoint"] == expected_midpoint_value
        )

    def test_date_valuation_first_added(self):
        date_today = date.today()
        barrier = BarrierFactory(
            status_date=date_today, status=BarrierStatus.OPEN_IN_PROGRESS
        )
        ts1 = datetime.datetime.now(tz=datetime.timezone.utc)
        with freezegun.freeze_time(ts1):
            eia = EconomicImpactAssessmentFactory(barrier=barrier, impact=6)

        ts2 = datetime.datetime.now(tz=datetime.timezone.utc)
        with freezegun.freeze_time(ts2):
            eia.impact = 7
            eia.save()

        data = DataWorkspaceSerializer(barrier).data

        assert ts2 > ts1
        assert data["date_valuation_first_added"] == ts2

    def test_valuation_assessment_midpoint_value(self):
        date_today = date.today()
        barrier = BarrierFactory(
            status_date=date_today, status=BarrierStatus.OPEN_IN_PROGRESS
        )
        impact_level = 6
        EconomicImpactAssessmentFactory(barrier=barrier, impact=impact_level)
        serialised_data = DataWorkspaceSerializer(barrier).data

        expected_midpoint = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[impact_level]
        expected_midpoint_value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC[
            expected_midpoint
        ]
        assert "valuation_assessment_midpoint_value" in serialised_data
        assert (
            serialised_data["valuation_assessment_midpoint_value"]
            == expected_midpoint_value
        )

    def test_mve_new_fields_in_dataworkspace(self):
        barrier = BarrierFactory(
            status_date=date.today(), status=BarrierStatus.OPEN_IN_PROGRESS
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        keys = serialised_data.keys()
        assert "start_date" in keys
        assert "export_types" in keys
        assert "is_currently_active" in keys
        assert "main_sector" in keys
        assert "export_description" in keys

    def test_priority_level_in_dataworkspace(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            status=BarrierStatus.OPEN_IN_PROGRESS,
            priority_level="NONE",
            top_priority_status="APPROVED",
        )
        serialised_data = DataWorkspaceSerializer(barrier).data
        assert "priority_level" in serialised_data.keys()
        assert serialised_data["priority_level"] == "PB100"

    def test_date_of_priority_level_none(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            priority_level=PRIORITY_LEVELS.NONE,
        )
        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_priority_level"] is None

        barrier.priority_level = PRIORITY_LEVELS.COUNTRY
        barrier.save()
        barrier.priority_level = PRIORITY_LEVELS.NONE
        barrier.save()

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_priority_level"] is None

    def test_date_of_priority_level(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            priority_level=PRIORITY_LEVELS.NONE,
        )
        ts1 = datetime.datetime.now(tz=datetime.timezone.utc)
        with freezegun.freeze_time(ts1):
            barrier.priority_level = PRIORITY_LEVELS.COUNTRY
            barrier.save()

        # Make random change
        barrier.title = "test"
        barrier.save()
        barrier.summary = "summary"
        barrier.save()

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_priority_level"] == ts1

        ts2 = datetime.datetime.now(tz=datetime.timezone.utc)
        with freezegun.freeze_time(ts2):
            barrier.priority_level = PRIORITY_LEVELS.WATCHLIST
            barrier.save()

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_priority_level"] == ts2

    def test_date_of_top_priority_scoping_none(self):
        priority_tag = BarrierTag.objects.get(
            title="Scoping (Top 100 priority barrier)"
        )
        barrier = BarrierFactory(status_date=date.today())

        barrier.tags.add(priority_tag)
        barrier.tags.remove(priority_tag)

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_top_priority_scoping"] is None

    def test_date_of_top_priority_scoping(self):
        priority_tag = BarrierTag.objects.get(
            title="Scoping (Top 100 priority barrier)"
        )
        barrier = BarrierFactory(status_date=date.today())

        ts1 = datetime.datetime.now(tz=datetime.timezone.utc)
        with freezegun.freeze_time(ts1):
            barrier.tags.add(priority_tag)

        barrier.title = "test"
        barrier.save()

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_top_priority_scoping"] is ts1

        barrier.tags.remove(priority_tag)
        ts2 = datetime.datetime.now(tz=datetime.timezone.utc)
        with freezegun.freeze_time(ts2):
            barrier.tags.add(priority_tag)

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_of_top_priority_scoping"] is ts2

    def test_estimated_resolution_date_first_added_none(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            estimated_resolution_date=None,
        )
        data = DataWorkspaceSerializer(barrier).data
        assert data["date_estimated_resolution_date_first_added"] is None

    def test_estimated_resolution_date_first_added(self):
        barrier = BarrierFactory(
            status_date=date.today(),
            estimated_resolution_date=None,
        )
        ts1 = date.today()
        with freezegun.freeze_time(ts1):
            barrier.estimated_resolution_date = ts1
            barrier.save()

        data = DataWorkspaceSerializer(barrier).data
        assert data["date_estimated_resolution_date_first_added"] == ts1.strftime(
            "%Y-%m-%d"
        )

        ts2 = ts1 + datetime.timedelta(days=1)
        with freezegun.freeze_time(ts2):
            barrier.estimated_resolution_date = ts2
            barrier.save()

        data = DataWorkspaceSerializer(barrier).data
        # Set as the first time ERD set (ts1, not ts2)
        assert data["date_estimated_resolution_date_first_added"] == ts1.strftime(
            "%Y-%m-%d"
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
