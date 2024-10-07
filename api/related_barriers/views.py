import logging

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.related_barriers import client
from api.related_barriers.serializers import BarrierRelatedListSerializer

logger = logging.getLogger(__name__)


@api_view(["GET"])
def related_barriers(request, pk) -> Response:
    """
    Return a list of related barriers
    """
    logger.info(f"Getting related barriers for {pk}")
    barrier = get_object_or_404(Barrier, pk=pk)

    barrier_ids = client.get_related_barriers(
        pk=str(barrier.pk), title=barrier.title, summary=barrier.summary
    )

    return Response(
        BarrierRelatedListSerializer(
            Barrier.objects.filter(id__in=barrier_ids), many=True
        ).data
    )


# @api_view(["GET"])
# def related_barriers_search(request) -> Response:
#     """
#     Return a list of related barriers given a search term/phrase
#     """
#
#     serializer = SearchRequest(data=request.GET)
#     serializer.is_valid(raise_exception=True)
#
#     if manager.manager is None:
#         manager.init()
#
#     barrier_scores = manager.manager.get_similar_barriers_searched(
#         search_term=serializer.data["search_term"],
#         similarity_threshold=SIMILARITY_THRESHOLD,
#         quantity=SIMILAR_BARRIERS_LIMIT,
#     )
#
#     barrier_ids = [b[0] for b in barrier_scores]
#
#     barriers = Barrier.objects.filter(id__in=barrier_ids).annotate(
#         barrier_id=Cast("id", output_field=CharField())
#     )
#     barriers = {b.barrier_id: b for b in barriers}
#
#     for barrier_id, score in barrier_scores:
#         barriers[barrier_id].similarity = score
#
#     data = [value for key, value in barriers.items()]
#     serializer = BarrierRelatedListSerializer(data, many=True)
#     return Response(serializer.data)
