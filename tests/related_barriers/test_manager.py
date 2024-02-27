import pytest

pytestmark = [pytest.mark.django_db]


def test_db(related_barrier_manager):
    barrier_ids = related_barrier_manager.get_barrier_ids()
    embeddings = related_barrier_manager.get_embeddings()

    assert embeddings == 1
    assert barrier_ids == 1
