import pytest

from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


def test_cosine_sim():
    barrier1 = BarrierFactory(priority="LOW")
    barrier2 = BarrierFactory(priority="MEDIUM")
    barrier3 = BarrierFactory(priority="HIGH")
    #
    # barrier1.summary = 'TEST'
    # barrier1.save()

    # assert 1 == 1

    # similarity_score_matrix = service.SimilarityScoreMatrix.create_matrix()

    from api.related_barriers import model

    db = model.create_db()

    assert len(db.get_cosine_sim()) == 3

    new_barrier = BarrierFactory(title='Test Title')
    data = {'id': new_barrier.id, 'barrier_corpus': f'{new_barrier.title}. {new_barrier.summary}'}
    model.add_barrier(data)
