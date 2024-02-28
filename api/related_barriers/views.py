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
from api.related_barriers.manager import RelatedBarrierManager
from api.related_barriers.serializers import BarrierRelatedListSerializer


@api_view(["GET"])
def related_barriers(request, pk) -> Response:
    """
    Return a list of related barriers
    """
    barrier = get_object_or_404(Barrier, pk=pk)
    similar_barrier_ids = manager.manager.get_similar_barriers(
        barrier=BarrierEntry(
            id=str(barrier.id),
            barrier_corpus=manager.barrier_to_corpus(barrier),
        ),
        similarity_threshold=SIMILARITY_THRESHOLD,
        quantity=SIMILAR_BARRIERS_LIMIT,
    )

    return Response(
        BarrierRelatedListSerializer(
            Barrier.objects.filter(id__in=similar_barrier_ids), many=True
        ).data
    )
