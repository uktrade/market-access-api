import pytest

from tests.barriers.factories import BarrierFactory
from api.related_barriers import service


pytestmark = [pytest.mark.django_db]


def test_related_barriers():
    barrier1 = BarrierFactory(priority="LOW")
    barrier2 = BarrierFactory(priority="MEDIUM")
    barrier3 = BarrierFactory(priority="HIGH")
    #
    # barrier1.summary = 'TEST'
    # barrier1.save()

    # assert 1 == 1

    similarity_score_matrix = service.SimilarityScoreMatrix.create_matrix()

    print("Hello___1")
    print(similarity_score_matrix)

    assert 0