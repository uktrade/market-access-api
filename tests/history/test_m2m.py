import pytest

from api.barriers.models import Barrier
from api.metadata.constants import OrganisationType
from api.metadata.models import Organisation
from tests.barriers.factories import CommodityFactory
from tests.metadata.factories import BarrierTagFactory

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def barrier(barrier):
    barrier.summary = "New summary"
    barrier.save()
    barrier.title = "New title"
    barrier.save()
    return barrier


@pytest.fixture
def organisation():
    return Organisation.objects.create(
        name="TestOrg", organisation_type=OrganisationType.MINISTERIAL_DEPARTMENTS
    )


def test_m2m_organisation(barrier, organisation):
    assert len(Barrier.get_history(barrier_id=barrier.id)) == 2
    assert organisation.name == "TestOrg"
    assert Barrier.history.filter(id=barrier.id).first().organisations_cache == []

    barrier.organisations.add(organisation)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)
    assert Barrier.history.filter(id=barrier.id).first().organisations_cache == [
        organisation.id
    ]
    assert len(v2_history) == 3

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "organisations",
        "model": "barrier",
        "new_value": [organisation.id],
        "old_value": [],
        "user": None,
    }

    new_orgs = Organisation.objects.all()[:2]
    barrier.refresh_from_db()
    barrier.organisations.add(*new_orgs)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)
    assert len(v2_history) == 4
    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "organisations",
        "model": "barrier",
        "new_value": [o.id for o in new_orgs] + [organisation.id],
        "old_value": [organisation.id],
        "user": None,
    }


def test_m2m_commodities(barrier):
    commodity = CommodityFactory(code="2105000000", description="Ice cream")
    barrier.commodities.add(commodity)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1] == {
        "model": "barrier",
        "date": v2_history[-1]["date"],
        "field": "commodities",
        "user": None,
        "old_value": [],
        "new_value": [
            {
                "code": "",
                "country": None,
                "commodity": {
                    "code": "2105000000",
                    "version": "2020-01-01",
                    "description": "Ice cream",
                    "full_description": "Ice cream",
                },
                "trading_bloc": None,
            }
        ],
    }

    commodity = CommodityFactory(code="2106000000", description="Snickers")
    barrier.refresh_from_db()
    barrier.commodities.add(commodity)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "commodities",
        "model": "barrier",
        "new_value": [
            {
                "code": "",
                "commodity": {
                    "code": "2105000000",
                    "description": "Ice cream",
                    "full_description": "Ice cream",
                    "version": "2020-01-01",
                },
                "country": None,
                "trading_bloc": None,
            },
            {
                "code": "",
                "commodity": {
                    "code": "2106000000",
                    "description": "Snickers",
                    "full_description": "Snickers",
                    "version": "2020-01-01",
                },
                "country": None,
                "trading_bloc": None,
            },
        ],
        "old_value": [
            {
                "code": "",
                "commodity": {
                    "code": "2105000000",
                    "description": "Ice cream",
                    "full_description": "Ice cream",
                    "version": "2020-01-01",
                },
                "country": None,
                "trading_bloc": None,
            }
        ],
        "user": None,
    }


def test_m2m_tags(barrier):
    assert len(Barrier.get_history(barrier_id=barrier.id)) == 2
    assert Barrier.history.filter(id=barrier.id).first().tags_cache == []

    new_tag = BarrierTagFactory(title="brouhaha")
    barrier.tags.add(new_tag)
    barrier.save()

    assert Barrier.history.filter(id=barrier.id).first().tags_cache == [new_tag.id]

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert len(v2_history) == 3
    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "model": "barrier",
        "field": "tags",
        "old_value": [],
        "new_value": [new_tag.id],
        "user": None,
    }

    new_tag_2 = BarrierTagFactory(title="brouhahaasdsad")
    barrier.tags.add(new_tag_2)
    barrier.tags.remove(new_tag)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert len(v2_history) == 4
    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "model": "barrier",
        "field": "tags",
        "old_value": [new_tag.id],
        "new_value": [new_tag_2.id],
        "user": None,
    }
