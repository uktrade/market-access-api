from uuid import UUID

import pytest

from api.barriers.models import Barrier
from api.metadata.constants import BARRIER_SOURCE
from api.metadata.models import BarrierPriority

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def barrier(barrier):
    barrier.summary = "New summary"
    barrier.save()
    barrier.title = "New title"
    barrier.save()
    return barrier


def assert_and_get_initial_history(barrier):
    v2_history = Barrier.get_history(barrier_id=barrier.id)
    # from pprint import pprint
    # print('HIUSOTY')
    # pprint(v2_history)
    assert v2_history == [
        {
            "date": v2_history[0]["date"],
            "field": "summary",
            "model": "barrier",
            "new_value": "New summary",
            "old_value": "Some problem description.",
            "user": None,
        },
        {
            "date": v2_history[1]["date"],
            "field": "title",
            "model": "barrier",
            "new_value": "New title",
            "old_value": "TEST BARRIER",
            "user": None,
        },
    ]

    return v2_history


def test_assert_and_get_initial_history(barrier):
    assert_and_get_initial_history(barrier)


def test_group_by_priority_history(barrier):
    initial_history = assert_and_get_initial_history(barrier)
    barrier.priority = BarrierPriority.objects.get(code="HIGH")
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history == initial_history + [
        {
            "date": v2_history[len(initial_history)]["date"],
            "field": "priority",
            "model": "barrier",
            "new_value": {"priority": 2, "priority_summary": ""},
            "old_value": {"priority": 1, "priority_summary": ""},
            "user": None,
        }
    ]


def test_group_by_source(barrier):
    initial_history = assert_and_get_initial_history(barrier)
    barrier.source = BARRIER_SOURCE.TRADE
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history == initial_history + [
        {
            "date": v2_history[-1]["date"],
            "field": "source",
            "model": "barrier",
            "new_value": {"other_source": "", "source": "TRADE"},
            "old_value": {"other_source": "", "source": "COMPANY"},
            "user": None,
        }
    ]


def test_group_by_sectors(barrier):
    initial_history = assert_and_get_initial_history(barrier)
    barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    from pprint import pprint

    print("HIUSOTY")
    pprint(v2_history)

    assert v2_history == initial_history + [
        {
            "model": "barrier",
            "date": v2_history[-1]["date"],
            "field": "sectors",
            "user": None,
            "old_value": {
                "sectors": [UUID("af959812-6095-e211-a939-e4115bead28a")],
                "all_sectors": None,
            },
            "new_value": {
                "sectors": [UUID("9538cecc-5f95-e211-a939-e4115bead28a")],
                "all_sectors": None,
            },
        }
    ]
