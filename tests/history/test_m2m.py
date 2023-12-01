import pytest

from api.barriers.models import Barrier
from api.metadata.constants import OrganisationType
from api.metadata.models import Organisation

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
    assert Organisation.history.filter(id=organisation.id).count() == 1
    assert len(Barrier.get_history(barrier_id=barrier.id)) == 4
    assert organisation.name == "TestOrg"
    assert Barrier.history.filter(id=barrier.id).first().organisations_cache == []

    barrier.organisations.add(organisation)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)
    assert Barrier.history.filter(id=barrier.id).first().organisations_cache == [
        organisation.id
    ]
    assert len(v2_history) == 5

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
    assert len(v2_history) == 6
    assert v2_history[-1] == {
        "date": v2_history[-1]["date"],
        "field": "organisations",
        "model": "barrier",
        "new_value": [o.id for o in new_orgs] + [organisation.id],
        "old_value": [organisation.id],
        "user": None,
    }
