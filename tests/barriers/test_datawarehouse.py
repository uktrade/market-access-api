from datetime import date

import pytest
from api.barriers.serializers.data_workspace import DataWorkspaceSerializer
from api.core.test_utils import create_test_user
from django.test import TestCase
from tests.action_plans.factories import (
    ActionPlanFactory,
    ActionPlanMilestoneFactory,
    ActionPlanTaskFactory,
)
from tests.barriers.factories import BarrierFactory
from tests.user.factories import UserFactoryMixin

pytestmark = [pytest.mark.django_db]


class TestDataWarehouseExport(UserFactoryMixin, TestCase):
    def setUp(self):
        super().setUp()

    def test_datawarehouse_action_plans_values(self):

        owner = create_test_user()

        barrier = BarrierFactory(status_date=date.today())
        action_plan = ActionPlanFactory(barrier=barrier, owner=owner)
        milestone = ActionPlanMilestoneFactory(action_plan=action_plan)
        task = ActionPlanTaskFactory(milestone=milestone)

        # barrier = BarrierFactory(status_date=date.today())
        # action_plan = barrier.action_plan
        # assert self.barrier.current_economic_assessment == clear1
        serializer = DataWorkspaceSerializer(barrier)
        serializer.data
        assert serializer.data == {}
