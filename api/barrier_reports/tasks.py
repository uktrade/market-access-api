from typing import List

from celery import shared_task

from api.barrier_reports import service


@shared_task
def generate_s3_and_send_email(
    barrier_report_id: str,
    barrier_ids: List[str],
):
    return service.generate_s3_and_send_email(
        barrier_report_id=barrier_report_id,
        barrier_ids=barrier_ids,
    )
