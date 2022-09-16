import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from api.action_plans.models import ActionPlan
from tests.action_plans.factories import ActionPlanMilestoneFactory
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


class TestActionPlanFilters(TestCase):
    def setUp(self):
        barriers = BarrierFactory.create_batch(10)

    def test_fresh_barriers_have_no_active_action_plans(self):
        active_action_plans = ActionPlan.objects.get_active_action_plans().all()

        self.assertEqual(len(active_action_plans), 0)

        active_action_plans_exist = (
            ActionPlan.objects.get_active_action_plans().exists()
        )

        self.assertEqual(active_action_plans_exist, False)

    def _active_count(self):
        return ActionPlan.objects.get_active_action_plans().all().count()

    def test_activation_of_action_plan_by_field(self):

        # barriers = BarrierFactory.create_batch(10)
        self.assertEqual(ActionPlan.objects.get_active_action_plans().exists(), False)

        # barrier = Barrier.objects.first()
        action_plan: ActionPlan = ActionPlan.objects.first()

        # add a milestone to
        milestone = ActionPlanMilestoneFactory(
            action_plan=action_plan,
        )

        num_active_action_plans = ActionPlan.objects.get_active_action_plans().count()
        self.assertEqual(num_active_action_plans, 1)

        self.assertEqual(self._active_count(), 1)

        milestone.delete()
        self.assertEqual(self._active_count(), 0)

        # test for:
        # current_status
        # current_status_last_updated
        # status
        # strategic_context
        # strategic_context_last_updated
        # has_risks
        # potential_unwanted_outcomes
        # potential_risks
        # risk_level
        # risk_mitigation_measures

        ActionPlan.objects.filter(id=action_plan.id).update(current_status="test")
        self.assertEqual(self._active_count(), 1)

        # skip the save method
        ActionPlan.objects.filter(id=action_plan.id).update(current_status="")
        self.assertEqual(self._active_count(), 0)

        ActionPlan.objects.filter(id=action_plan.id).update(status="test")
        self.assertEqual(self._active_count(), 1)

        # skip the save method
        ActionPlan.objects.filter(id=action_plan.id).update(status="")
        self.assertEqual(self._active_count(), 0)

        ActionPlan.objects.filter(id=action_plan.id).update(strategic_context="test")
        self.assertEqual(self._active_count(), 1)

        # skip the save method
        ActionPlan.objects.filter(id=action_plan.id).update(strategic_context="")
        self.assertEqual(self._active_count(), 0)

        ActionPlan.objects.filter(id=action_plan.id).update(has_risks="test")
        self.assertEqual(self._active_count(), 1)

        # skip the save method
        ActionPlan.objects.filter(id=action_plan.id).update(has_risks="")
        self.assertEqual(self._active_count(), 0)

        user = User(
            username=User.objects.make_random_password(),
            first_name="TestFirst",
            last_name="TestLast",
        )
        user.save()
        ActionPlan.objects.filter(id=action_plan.id).update(owner=user)

        self.assertEqual(self._active_count(), 1)

        ActionPlan.objects.filter(id=action_plan.id).update(owner=None)
        self.assertEqual(self._active_count(), 0)
