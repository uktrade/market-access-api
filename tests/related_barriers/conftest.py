import mock
import pytest
from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat

from api.barriers.models import Barrier
from api.related_barriers.manager import RelatedBarrierManager
from tests.barriers.factories import BarrierFactory


@pytest.fixture
def related_barrier_manager_context():
    # BarrierFactory(title='title 1')
    BarrierFactory(title="title 2")
    data = (
        Barrier.objects.filter(archived=False)
        .exclude(draft=True)
        .annotate(
            barrier_corpus=Concat("title", V(". "), "summary", output_field=CharField())
        )
        .values("id", "barrier_corpus")
    )
    with mock.patch('api.related_barriers.manager.cache') as mock_cache:
        with mock.patch('api.related_barriers.manager.get_transformer') as mock_get_transformer:
            yield RelatedBarrierManager(data), mock_cache, mock_get_transformer
