from datetime import datetime

import pytest

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.core.test_utils import create_test_user
from api.dashboard.views import get_tasks, get_combined_barrier_mention_qs
from api.interactions.models import Mention
from api.metadata.models import BarrierTag, ExportType
from tests.barriers.factories import BarrierFactory
from django.contrib.auth.models import Group


pytestmark = [pytest.mark.django_db]


def test_get_tasks():
    user = create_test_user()
    user.groups.add(Group.objects.get(name="Publisher"))
    user.groups.add(Group.objects.get(name="Public barrier approver"))
    tag = BarrierTag.objects.get(title="Programme Fund - Facilitative Regional")
    tag2 = BarrierTag.objects.first()
    barrier: Barrier = BarrierFactory()
    export_type = ExportType.objects.get(name="goods")
    barrier.export_types.add(export_type)
    barrier.tags.add(tag)
    barrier.tags.add(tag2)
    barrier.public_barrier.public_view_status = 20
    barrier.public_barrier.title = "Title1"
    barrier.public_barrier.summary = "Summary1"
    barrier.public_barrier.set_to_allowed_on = datetime.now()
    barrier.public_barrier.save()
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    tasks = get_tasks(user)

    assert len(tasks) == 1


def test_get_combined_barrier_mention_qs():
    user = create_test_user()
    user2 = create_test_user()
    barrier_1: Barrier = BarrierFactory()
    barrier_2: Barrier = BarrierFactory()
    team_member_1 = TeamMember.objects.create(
        barrier=barrier_1, user=user, created_by=user, role=TeamMember.OWNER
    )
    team_member_2 = TeamMember.objects.create(
        barrier=barrier_2, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier_1.barrier_team.add(team_member_1)
    barrier_2.barrier_team.add(team_member_2)
    Mention.objects.create(created_by=user2, barrier=barrier_2, recipient=user)

    qs = get_combined_barrier_mention_qs(user)

    assert list(qs.values_list("id", flat=True)) == [barrier_2.id, barrier_1.id]
