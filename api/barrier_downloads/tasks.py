import logging
from typing import List

from celery import shared_task

from api.barrier_downloads import service

logger = logging.getLogger(__name__)


@shared_task
def generate_barrier_download_file(
    barrier_download_id: str,
    barrier_ids: List[str],
):
    import time

    from django.db import connection

    start = time.time()
    before = len(connection.queries)
    service.generate_barrier_download_file(
        barrier_download_id=barrier_download_id,
        barrier_ids=barrier_ids,
    )
    after = len(connection.queries)
    end = time.time()
    logger.info(f"[RBSQL]: {after - before} queries run")
    logger.info(f"[RBSQL]: {end - start}s")


@shared_task
def barrier_download_complete_notification(barrier_download_id: str):
    service.barrier_download_complete_notification(
        barrier_download_id=barrier_download_id
    )
