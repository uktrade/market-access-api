import datetime

from pytest import fixture

from api.barriers.models import Barrier
from api.metadata.models import BarrierTag, BarrierPriority
from tests.history.factories import BarrierFactory


@fixture
def date_now():
    return datetime.datetime.now()


@fixture
def draft_barrier(date_now) -> Barrier:
    return BarrierFactory(
        start_date=date_now,
        estimated_resolution_date=date_now + datetime.timedelta(days=45)
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
