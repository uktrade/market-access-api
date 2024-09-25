import logging

from celery import shared_task
from django.core.management import call_command

from api.barriers.models import Barrier
from api.related_barriers import manager
from api.related_barriers.constants import BarrierEntry

logger = logging.getLogger(__name__)


def update_related_barrier(barrier_id: str):
    logger.info(f"Updating related barrier embeddings for:  {barrier_id}")
    related_barriers = manager.get_or_init()
    try:
        related_barriers.update_barrier(
            BarrierEntry(
                id=barrier_id,
                barrier_corpus=manager.barrier_to_corpus(
                    Barrier.objects.get(pk=barrier_id)
                ),
            )
        )
    except Exception as e:
        # We don't want barrier embedding updates to break worker so just log error
        logger.critical(str(e))


@shared_task
def reindex_related_barriers():
    """Schedule daily task to reindex"""
    call_command("related_barriers", "--reindex", "1")
