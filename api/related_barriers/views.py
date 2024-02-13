# from django.shortcuts import get_object_or_404
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
#
# from api.barriers.models import Barrier
# from api.related_barriers.serializers import BarrierRelatedListSerializer
# from api.related_barriers.service import SimilarityScoreMatrix
#
#
# @api_view(["GET"])
# def related_barriers(request, pk) -> Response:
#     """
#     Return a list of related barriers
#     """
#     barrier_object = get_object_or_404(Barrier, pk=pk)
#     similarity_score_matrix = SimilarityScoreMatrix.retrieve_matrix()
#     barriers = similarity_score_matrix.retrieve_similar_barriers(barrier_object)
#     serializer = BarrierRelatedListSerializer(barriers, many=True)
#     return Response(serializer.data)

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.related_barriers.serializers import BarrierRelatedListSerializer
from api.related_barriers.model import db
from api.related_barriers.service import SimilarityScoreMatrix

# Use celery Queue to manage race conditions when updating

@api_view(["GET"])
def related_barriers(request, pk) -> Response:
    """
    Return a list of related barriers
    """
    barrier_object = get_object_or_404(Barrier, pk=pk)
    similarity_score_matrix = SimilarityScoreMatrix.retrieve_matrix()
    barriers = similarity_score_matrix.retrieve_similar_barriers(barrier_object)
    serializer = BarrierRelatedListSerializer(barriers, many=True)
    return Response(serializer.data)