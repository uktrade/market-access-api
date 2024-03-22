import mock
import pytest

from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


def test_related_barrier_handler():
    barrier = BarrierFactory()

    with mock.patch('api.barriers.signals.handlers.related_barrier_update_embeddings') as mock_handler:
        with mock.patch('api.barriers.signals.handlers.manager') as mock_manager:
            barrier.title = 'New Title'
            barrier.save()

    assert mock_manager.manager.update_barrier.call_count == 1
