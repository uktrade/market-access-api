"""
Sanity tests that fields can be replaced:

TODO: Once approved, remove the fields from legacy history
"""
from uuid import UUID

import pytest

from api.barriers.models import Barrier
from api.history.factories import BarrierHistoryFactory
from api.history.v2.enrichment import (
    enrich_country,
    enrich_main_sector,
    enrich_priority_level,
    enrich_trade_category,
)

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
    initial_history = assert_and_get_initial_history(barrier)
    barrier.country = "82756b9a-5d95-e211-a939-e4115bead28a"
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    # Pre enrich
    assert v2_history == initial_history + [
        {
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
    ]

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
