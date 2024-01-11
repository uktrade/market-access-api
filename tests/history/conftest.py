import datetime

from pytest import fixture

from api.barriers.models import Barrier
from api.core.test_utils import create_test_user
from api.metadata.models import BarrierPriority, BarrierTag
from tests.history.factories import BarrierFactory


@fixture
def date_now():
    return datetime.datetime.now()


@fixture
def draft_barrier(date_now) -> Barrier:
    return BarrierFactory(
        start_date=date_now,
        companies=[],
    )


@fixture
def tags():
    return [BarrierTag.objects.get(title="BREXIT")]


@fixture
def priority():
    return BarrierPriority.objects.get(code="UNKNOWN")


@fixture
def barrier(draft_barrier: Barrier):
    draft_barrier.submit_report()
    return draft_barrier


@fixture
def user():
    return create_test_user(
        first_name="Hey",
        last_name="Siri",
        email="hey@siri.com",
        username="heysiri",
    )
