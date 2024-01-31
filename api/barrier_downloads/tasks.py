from typing import List

from celery import shared_task

from api.barrier_downloads import service


@shared_task
def generate_barrier_download_file(
    barrier_download_id: str,
    barrier_ids: List[str],
):
    return service.generate_barrier_download_file(
        barrier_download_id=barrier_download_id,
        barrier_ids=barrier_ids,
    )


@shared_task
def barrier_download_complete_notification(barrier_download_id: str):
    service.barrier_download_complete_notification(barrier_download_id=barrier_download_id)
