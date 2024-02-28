import mock
import pytest
from mock.mock import call

from api.related_barriers.constants import BarrierEntry

pytestmark = [pytest.mark.django_db]


def test_manager_calls_cache_get(related_barrier_manager_context):
    manager, cache, transformer = related_barrier_manager_context
    mock_values = ["hello", "world"]
    cache.get.side_effect = mock_values

    assert manager.get_barrier_ids() == mock_values[0]
    assert manager.get_embeddings() == mock_values[1]


def test_manager_calls_cache_set(related_barrier_manager_context):
    manager, cache, transformer = related_barrier_manager_context
    barrier_ids = [1]
    embeddings = ["2"]

    manager.set_barrier_ids(barrier_ids)
    manager.set_embeddings(embeddings)

    cache.set.assert_has_calls(
        [
            call("BARRIER_IDS_CACHE_KEY", barrier_ids, timeout=None),
            call("EMBEDDINGS_CACHE_KEY", embeddings, timeout=None),
        ]
    )


def test_get_similar_barriers(related_barrier_manager_context):
    manager, cache, transformer = related_barrier_manager_context

    barrier_ids = ["a", "b", "c"]
    cache.get.return_value = barrier_ids

    with mock.patch.object(manager, "get_cosine_sim") as mock_get_cosine_sim:
        mock_get_cosine_sim.return_value = [
            [1, 0.1, 0.3],
            [0.1, 1, 0.3],
            [0.3, 0.3, 1],
        ]
        barrier = BarrierEntry(id="a", barrier_corpus="test")

        response = manager.get_similar_barriers(
            barrier=barrier, similarity_threshold=0.15, quantity=3
        )

        assert response == ["c"]

        response = manager.get_similar_barriers(
            barrier=barrier, similarity_threshold=0.09, quantity=3
        )

        assert response == ["b", "c"]

        response = manager.get_similar_barriers(
            barrier=barrier, similarity_threshold=0.09, quantity=1
        )

        assert response == ["c"]


def test_add_barrier(related_barrier_manager_context):
    manager, cache, get_transformer = related_barrier_manager_context
    transformer = mock.Mock()
    get_transformer.return_value = transformer

    barrier = BarrierEntry(id="a", barrier_corpus="test")

    with mock.patch.object(
        manager, "encode_barrier_corpus"
    ) as mock_encode_barrier_corpus:
        barrier_ids = ["b", "c"]
        embeddings = [[1], [2]]
        new_embeddings = [3]
        mock_encode_barrier_corpus.return_value = new_embeddings
        cache.get.side_effect = [barrier_ids, embeddings, new_embeddings]

        manager.add_barrier(barrier)

        cache.set.call_count == 2


def test_remove_barrier(related_barrier_manager_context):
    manager, cache, transformer = related_barrier_manager_context

    barrier_ids = ["a", "b", "c"]
    cache.get.return_value = barrier_ids

    with mock.patch.object(manager, "get_embeddings") as mock_get_embeddings:
        mock_get_embeddings.return_value = [
            [0.1, 0.3],
            [0.01, 0.71],
            [0.31, 0.11],
        ]
        barrier = BarrierEntry(id="b", barrier_corpus="test")

        manager.remove_barrier(barrier=barrier)

        cache.set.call_count == 2
