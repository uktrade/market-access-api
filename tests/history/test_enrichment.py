"""
Sanity tests that fields can be replaced:

TODO: Once approved, remove the fields from legacy history
"""
from uuid import UUID

import pytest

from api.barriers.models import Barrier, BarrierTopPrioritySummary
from api.collaboration.models import TeamMember
from api.history.v2.enrichment import (
    enrich_country,
    enrich_main_sector,
    enrich_priority_level,
    enrich_sectors,
    enrich_top_priority_status,
    enrich_trade_category, enrich_team_member_user,
)
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS

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


def test_country_enrichment(barrier):
    barrier.country = "82756b9a-5d95-e211-a939-e4115bead28a"
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id, enrich=False)

    # Pre enrich
    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "country",
        "model": "barrier",
        "new_value": {
            "admin_areas": [],
            "caused_by_trading_bloc": None,
            "country": UUID("82756b9a-5d95-e211-a939-e4115bead28a"),
            "trading_bloc": "",
        },
        "old_value": {
            "admin_areas": [],
            "caused_by_trading_bloc": None,
            "country": UUID("985f66a0-5d95-e211-a939-e4115bead28a"),
            "trading_bloc": "",
        },
        "user": None,
    }

    # enrich
    enrich_country(v2_history)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "location",
        "model": "barrier",
        "new_value": "France",
        "old_value": "Angola",
        "user": None,
    }


def test_trade_category_enrichment(barrier):
    initial_history = assert_and_get_initial_history(barrier)
    barrier.trade_category = "GOODS"
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "trade_category",
        "model": "barrier",
        "new_value": "GOODS",
        "old_value": "",
        "user": None,
    }

    enrich_trade_category(v2_history)

    assert v2_history == initial_history + [
        {
            "date": v2_history[-1]["date"],
            "field": "trade_category",
            "model": "barrier",
            "old_value": None,
            "new_value": {
                "id": "GOODS",
                "name": "Goods",
            },
            "user": None,
        }
    ]

    barrier.trade_category = "PROCUREMENT"
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)
    enrich_trade_category(v2_history)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "trade_category",
        "model": "barrier",
        "old_value": {
            "id": "GOODS",
            "name": "Goods",
        },
        "new_value": {
            "id": "PROCUREMENT",
            "name": "Procurement",
        },
        "user": None,
    }


def test_main_sector_enrichment(barrier):
    barrier.main_sector = "9538cecc-5f95-e211-a939-e4115bead28a"
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "main_sector",
        "model": "barrier",
        "new_value": UUID("9538cecc-5f95-e211-a939-e4115bead28a"),
        "old_value": UUID("355f977b-8ac3-e211-a646-e4115bead28a"),
        "user": None,
    }

    enrich_main_sector(v2_history)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "main_sector",
        "model": "barrier",
        "new_value": "Aerospace",
        "old_value": "Consumer and retail",
        "user": None,
    }


def test_priority_level_enrichment(barrier):
    initial_history = assert_and_get_initial_history(barrier)
    barrier.priority_level = "WATCHLIST"
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "priority_level",
        "model": "barrier",
        "new_value": "WATCHLIST",
        "old_value": "NONE",
        "user": None,
    }

    enrich_priority_level(v2_history)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "priority_level",
        "model": "barrier",
        "new_value": "Watch list",
        "old_value": "",
        "user": None,
    }


def test_top_priority_status_enrichment(barrier):
    barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING
    barrier.save()

    v2_barrier_history = Barrier.get_history(barrier_id=barrier.id)

    # Pre enrich
    assert v2_barrier_history[-1] == {
        "date": v2_barrier_history[-1]["date"],
        "field": "top_priority_status",
        "model": "barrier",
        "new_value": {
            "top_priority_rejection_summary": None,
            "top_priority_status": "APPROVAL_PENDING",
        },
        "old_value": {
            "top_priority_rejection_summary": None,
            "top_priority_status": "NONE",
        },
        "user": None,
    }
    BarrierTopPrioritySummary.objects.create(
        top_priority_summary_text="Has been approved", barrier=barrier
    )
    barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVED
    barrier.save()
    v2_history = Barrier.get_history(barrier_id=barrier.id)
    v2_top_priority_summary_history = BarrierTopPrioritySummary.get_history(
        barrier_id=barrier.id
    )

    # Enrich
    enrich_top_priority_status(
        barrier_history=v2_history,
        top_priority_summary_history=v2_top_priority_summary_history,
    )

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "top_priority_status",
        "model": "barrier",
        "new_value": {"reason": "Has been approved", "value": "Top 100 Priority"},
        "old_value": {"reason": "", "value": "Top 100 Approval Pending"},
        "user": None,
    }


def test_sectors_enrichment(barrier):
    barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
    barrier.save()

    history = Barrier.get_history(barrier_id=barrier.pk)

    assert history[-1] == {
        "date": history[-1]["date"],
        "model": "barrier",
        "field": "sectors",
        "old_value": {
            "all_sectors": None,
            "sectors": [UUID("af959812-6095-e211-a939-e4115bead28a")],
        },
        "new_value": {
            "all_sectors": None,
            "sectors": [UUID("9538cecc-5f95-e211-a939-e4115bead28a")],
        },
        "user": None,
    }

    enrich_sectors(history)

    assert history[-1] == {
        "date": history[-1]["date"],
        "model": "barrier",
        "field": "sectors",
        "old_value": {
            "all_sectors": None,
            "sectors": ["af959812-6095-e211-a939-e4115bead28a"],
        },
        "new_value": {
            "all_sectors": None,
            "sectors": ["9538cecc-5f95-e211-a939-e4115bead28a"],
        },
        "user": None,
    }


def test_team_members_enrichment(barrier, user):
    TeamMember.objects.create(
        barrier=barrier, user=user, role="Contributor"
    )

    history = TeamMember.get_history(barrier_id=barrier.pk)

    assert history == [
        {
            'date': history[0]['date'],
            'field': 'user',
            'model': 'team_member',
            'new_value': {
                'user': user.id,
                'user__first_name': 'Hey',
                'user__last_name': 'Siri',
                'user__email': 'hey@siri.com',
                'user__username': 'heysiri',
                "role": "Contributor"
            },
            'old_value': {
                'user': None,
                'user__first_name': None,
                'user__last_name': None,
                'user__email': None,
                'user__username': None,
                "role": None
            },
            'user': None,
        }
    ]

    enrich_team_member_user(history)

    assert history == [
        {
            'date': history[0]['date'],
            'field': 'user',
            'model': 'team_member',
            'new_value': {'role': 'Contributor', 'user': {'id': user.id, 'name': 'Hey Siri'}},
            'old_value': None,
            'user': None
        }
    ]
