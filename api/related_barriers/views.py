from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.related_barriers import model
from api.related_barriers.serializers import BarrierRelatedListSerializer


# Use celery Queue to manage race conditions when updating

@api_view(["GET"])
def related_barriers(request, pk) -> Response:
    """
    Return a list of related barriers
    """
    if model.db is None:
        db = model.create_db()
        model.set_db(database=db)

    barrier = get_object_or_404(Barrier, pk=pk)
    barrier = {'id': str(barrier.id), 'barrier_corpus': model.barrier_to_corpus(barrier)}

    similar_barrier_ids = model.get_similar_barriers(barrier)

    return Response(
        BarrierRelatedListSerializer(
            Barrier.objects.filter(id__in=similar_barrier_ids),
            many=True
        ).data
    )
