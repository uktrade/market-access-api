import mock
import pytest

from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


def test_related_barrier_handler():
    barrier = BarrierFactory()

    with mock.patch(
        "api.barriers.signals.handlers.update_related_barrier"
    ) as mock_update_related_barrier:
        barrier.title = "New Title"
        barrier.save()

    mock_update_related_barrier.assert_called_once_with(barrier_id=str(barrier.pk))
