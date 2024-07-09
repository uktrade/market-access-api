import pytest
from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat

from api.barriers.models import Barrier
from tests.barriers.factories import BarrierFactory


@pytest.fixture
def related_barrier_manager_context():
    BarrierFactory(title="title 2")
    return (
        Barrier.objects.filter(archived=False)
        .exclude(draft=True)
        .annotate(
            barrier_corpus=Concat("title", V(". "), "summary", output_field=CharField())
        )
        .values("id", "barrier_corpus")
    )
