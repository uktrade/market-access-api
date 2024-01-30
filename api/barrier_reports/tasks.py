from typing import List

from celery import shared_task

from api.barrier_reports import service


@shared_task
def generate_barrier_report_file(
    barrier_report_id: str,
    barrier_ids: List[str],
):
    return service.generate_barrier_report_file(
        barrier_report_id=barrier_report_id,
        barrier_ids=barrier_ids,
    )


@shared_task
def barrier_report_complete_notification(barrier_report_id: str):
    service.barrier_report_complete_notification(barrier_report_id=barrier_report_id)
