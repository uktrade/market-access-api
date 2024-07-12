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

    # client.seed()

    barrier_ids = client.get_related_barriers(
        pk=str(barrier.pk), title=barrier.title, summary=barrier.summary
    )

    return Response(
        BarrierRelatedListSerializer(
            Barrier.objects.filter(id__in=barrier_ids), many=True
        ).data
    )
