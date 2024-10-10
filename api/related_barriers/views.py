import logging

from django.db.models import Case, CharField, FloatField, Value, When
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.related_barriers import manager
from api.related_barriers.constants import (
    SIMILAR_BARRIERS_LIMIT,
    SIMILARITY_THRESHOLD,
    BarrierEntry,
)
from api.related_barriers.serializers import BarrierRelatedListSerializer, SearchRequest

logger = logging.getLogger(__name__)


@api_view(["GET"])
def related_barriers_view(request, pk) -> Response:
    """
    Return a list of related barriers
    """
    logger.info(f"Getting related barriers for {pk}")
    barrier = get_object_or_404(Barrier, pk=pk)

    related_barriers = manager.get_or_init()

    barrier_scores = related_barriers.get_similar_barriers(
        barrier=BarrierEntry(
            id=str(barrier.id),
            barrier_corpus=manager.barrier_to_corpus(barrier),
        ),
        similarity_threshold=SIMILARITY_THRESHOLD,
        quantity=10,
    )

    barrier_ids = [b[0] for b in barrier_scores]
    when_tensor = [When(id=k, then=Value(v.item())) for k, v in barrier_scores]

    similar_barriers = (
        Barrier.objects.filter(id__in=barrier_ids)
        .annotate(similarity=Case(*when_tensor, output_field=FloatField()))
        .order_by("-similarity")
    )

    serializer = BarrierRelatedListSerializer(similar_barriers, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def related_barriers_search(request) -> Response:
    """
    Return a list of related barriers given a search term/phrase
    """

    serializer = SearchRequest(data=request.GET)
    serializer.is_valid(raise_exception=True)

    related_barriers = manager.get_or_init()

    barrier_scores = related_barriers.get_similar_barriers_searched(
        search_term=serializer.data["search_term"],
        similarity_threshold=SIMILARITY_THRESHOLD,
        quantity=SIMILAR_BARRIERS_LIMIT,
    )

    barrier_ids = [b[0] for b in barrier_scores]

    barriers = Barrier.objects.filter(id__in=barrier_ids).annotate(
        barrier_id=Cast("id", output_field=CharField())
    )
    barriers = {b.barrier_id: b for b in barriers}

    for barrier_id, score in barrier_scores:
        barriers[barrier_id].similarity = score

    data = [value for key, value in barriers.items()]
    serializer = BarrierRelatedListSerializer(data, many=True)
    return Response(serializer.data)
