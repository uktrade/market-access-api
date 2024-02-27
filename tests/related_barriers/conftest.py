import pytest
from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat

from api.barriers.models import Barrier
from api.related_barriers.manager import RelatedBarrierManager
from tests.barriers.factories import BarrierFactory


@pytest.fixture
def related_barrier_manager():
    # BarrierFactory(title='title 1')
    print(BarrierFactory(title="title 1").pk)
    BarrierFactory(title="title 2")
    data = (
        Barrier.objects.filter(archived=False)
        .exclude(draft=True)
        .annotate(
            barrier_corpus=Concat("title", V(". "), "summary", output_field=CharField())
        )
        .values("id", "barrier_corpus")
    )
    return RelatedBarrierManager(data)
