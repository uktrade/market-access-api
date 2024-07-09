import mock
import pytest

from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


def test_related_barrier_handler():
    barrier = BarrierFactory()

    with mock.patch("api.barriers.signals.handlers.client") as mock_client:
        barrier.title = "New Title"
        barrier.save()

    mock_client.get_related_barriers.assert_called_once_with(
        pk=str(barrier.pk), title=barrier.title, summary=barrier.summary
    )
