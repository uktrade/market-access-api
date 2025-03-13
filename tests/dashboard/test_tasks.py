from datetime import date, datetime, timedelta

import pytest
from django.contrib.auth.models import Group

from api.barriers.models import (
    Barrier,
    BarrierProgressUpdate,
    ProgrammeFundProgressUpdate,
)
from api.collaboration.models import TeamMember
from api.core.test_utils import create_test_user
from api.dashboard.service import get_combined_barrier_mention_qs, get_tasks
from api.interactions.models import Mention
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS
from api.metadata.models import BarrierTag, ExportType
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


def test_editor_tasks():
    user = create_test_user()
    barrier: Barrier = BarrierFactory()
    barrier.public_barrier.public_view_status = 20
    barrier.public_barrier.save()
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    tasks = get_tasks(user)

    assert tasks[0]["task_list"][0]["tag"] == "PUBLICATION REVIEW"

    barrier.public_barrier.set_to_allowed_on = date.today() - timedelta(days=31)
    barrier.public_barrier.save()
    tasks = get_tasks(user)

    assert tasks[0]["task_list"][0]["tag"] == "OVERDUE REVIEW"


def test_create_add_priority_erd_task():
    user = create_test_user()
    barrier: Barrier = BarrierFactory(
        priority_level="OVERSEAS", estimated_resolution_date=None
    )
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    tasks = get_tasks(user)

    # assert 0
    assert tasks[0]["task_list"] == [
        {
            "link_text": "Add a quarterly progress update",
            "message": [
                "Add a quarterly progress update",
                "to this overseas delivery barrier.",
            ],
            "tag": "PROGRESS UPDATE DUE",
            "task_url": "barriers:add_progress_update",
        },
        {
            "link_text": "Check and add any other government departments " "(OGDs)",
            "message": [
                "Check and add any other government departments " "(OGDs)",
                "involved in the resolution of this barrier.",
            ],
            "tag": "ADD INFORMATION",
            "task_url": "barriers:edit_gov_orgs",
        },
        {
            "link_text": "Add an estimated resolution date",
            "message": [
                "Add an estimated resolution date",
                "to this Overseas Delivery barrier.",
            ],
            "tag": "ADD DATE",
            "task_url": "barriers:add_estimated_resolution_date",
        },
    ]


def test_create_add_overseas_priority_erd_task():
    user = create_test_user()
    barrier: Barrier = BarrierFactory(
        priority_level="OVERSEAS", estimated_resolution_date=None
    )
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    tasks = get_tasks(user)

    # assert 0
    assert tasks[0]["task_list"] == [
        {
            "link_text": "Add a quarterly progress update",
            "message": [
                "Add a quarterly progress update",
                "to this overseas delivery barrier.",
            ],
            "tag": "PROGRESS UPDATE DUE",
            "task_url": "barriers:add_progress_update",
        },
        {
            "link_text": "Check and add any other government departments " "(OGDs)",
            "message": [
                "Check and add any other government departments " "(OGDs)",
                "involved in the resolution of this barrier.",
            ],
            "tag": "ADD INFORMATION",
            "task_url": "barriers:edit_gov_orgs",
        },
        {
            "link_text": "Add an estimated resolution date",
            "message": [
                "Add an estimated resolution date",
                "to this Overseas Delivery barrier.",
            ],
            "tag": "ADD DATE",
            "task_url": "barriers:add_estimated_resolution_date",
        },
    ]


def test_create_add_pb100_priority_erd_task():
    user = create_test_user()
    barrier: Barrier = BarrierFactory(
        top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED,
        estimated_resolution_date=None,
    )
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    tasks = get_tasks(user)

    # assert 0
    assert tasks[0]["task_list"][2] == {
        "link_text": "Add an estimated resolution date",
        "message": ["Add an estimated resolution date", "to this PB100 barrier."],
        "tag": "ADD DATE",
        "task_url": "barriers:add_estimated_resolution_date",
    }


def test_create_review_priority_erd_task():
    user = create_test_user()
    barrier: Barrier = BarrierFactory(
        top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED,
        estimated_resolution_date=None,
    )
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    progress_update = BarrierProgressUpdate(barrier=barrier)
    progress_update.modified_on = datetime.now() - timedelta(days=181)
    progress_update.save()

    tasks = get_tasks(user)

    assert len(tasks[0]["task_list"]) == 4
    assert tasks[0]["task_list"][0]["tag"] in [
        "OVERDUE PROGRESS UPDATE",
        "PROGRESS UPDATE DUE",
    ]
    assert tasks[0]["task_list"][1]["tag"] == "ADD INFORMATION"
    assert tasks[0]["task_list"][2]["tag"] == "ADD DATE"
    assert tasks[0]["task_list"][3]["tag"] == "REVIEW DATE"


def test_create_add_progress_update_task():
    user = create_test_user()
    estimated_resolution_date = date(year=2024, month=12, day=12)
    barrier: Barrier = BarrierFactory(
        estimated_resolution_date=estimated_resolution_date
    )
    barrier.public_barrier.public_view_status = 20
    barrier.public_barrier.save()
    team_member = TeamMember.objects.create(
        barrier=barrier, user=user, created_by=user, role=TeamMember.OWNER
    )
    barrier.barrier_team.add(team_member)
    barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVED
    barrier.save()
    progress_update = ProgrammeFundProgressUpdate(barrier=barrier)
    progress_update.milestones_and_deliverables = "hello"
    progress_update.modified_on = datetime.now() - timedelta(days=91)
    progress_update.save()

    tasks = get_tasks(user)

    assert tasks[0]["task_list"][-2] == {
        "link_text": "Add your delivery confidence",
        "message": ["Add your delivery confidence", "to this barrier."],
        "tag": "ADD INFORMATION",
        "task_url": "barriers:add_progress_update",
    }


def test_get_tasks():
    user = create_test_user()
    user.groups.add(Group.objects.get(name="Publisher"))
    user.groups.add(Group.objects.get(name="Public barrier approver"))
    tag = BarrierTag.objects.get(title="Programme Fund - Facilitative Regional")
    tag2 = BarrierTag.objects.first()
    estimated_resolution_date = date(year=2024, month=12, day=12)
    barrier: Barrier = BarrierFactory(
        estimated_resolution_date=estimated_resolution_date
    )
    progress_update = ProgrammeFundProgressUpdate(barrier=barrier)
    progress_update.milestones_and_deliverables = "hello"
    progress_update.modified_on = datetime.now() - timedelta(days=91)
    progress_update.save()
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

    assert tasks[0]["task_list"] == [
        {
            "link_text": "Submit for clearance checks and GOV.UK publication approval",
            "message": [
                "Submit for clearance checks and GOV.UK publication approval",
                f'by {(barrier.public_barrier.set_to_allowed_on + timedelta(days=30)).strftime("%d %B %Y")}.',
            ],
            "tag": "PUBLICATION REVIEW",
            "task_url": "barriers:public_barrier_detail",
        },
        {
            "link_text": "Add a programme fund update",
            "message": ["Add a programme fund update", "to this barrier."],
            "tag": "PROGRESS UPDATE DUE",
            "task_url": "barriers:add_programme_fund_progress_update",
        },
        {
            "link_text": "Add an HS code to this barrier.",
            "message": ["Add an HS code to this barrier."],
            "tag": "ADD INFORMATION",
            "task_url": "barriers:edit_commodities",
        },
        {
            "link_text": "Check and add any other government departments (OGDs)",
            "message": [
                "Check and add any other government departments (OGDs)",
                "involved in the resolution of this barrier.",
            ],
            "tag": "ADD INFORMATION",
            "task_url": "barriers:edit_gov_orgs",
        },
        {
            "link_text": "Add your delivery confidence",
            "message": ["Add your delivery confidence", "to this barrier."],
            "tag": "ADD INFORMATION",
            "task_url": "barriers:add_progress_update",
        },
        {
            "link_text": "Review the estimated resolution date",
            "message": [
                "Review the estimated resolution date",
                f"as it is currently listed as {estimated_resolution_date},",
                "which is in the past.",
            ],
            "tag": "CHANGE OVERDUE",
            "task_url": "barriers:edit_estimated_resolution_date",
        },
    ]


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


def test_get_mention_non_team_member():
    user = create_test_user()
    user2 = create_test_user()
    barrier_1: Barrier = BarrierFactory()

    Mention.objects.create(created_by=user2, barrier=barrier_1, recipient=user)

    tasks = get_tasks(user)

    assert len(tasks) == 1
    assert len(tasks[0]["task_list"]) == 1
    assert tasks[0]["task_list"][0]["tag"] == "REVIEW COMMENT"
