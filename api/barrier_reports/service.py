import csv
import io
import logging
from typing import List

from django.conf import settings
from django.utils.timezone import now
from notifications_python_client import NotificationsAPIClient

from api.barrier_reports import tasks
from api.barrier_reports.constants import BARRIER_FIELD_TO_REPORT_TITLE
from api.barrier_reports.csv import _transform_csv_row
from api.barrier_reports.exceptions import BarrierReportDoesNotExist, BarrierReportNotificationError
from api.barrier_reports.models import BarrierReport, BarrierReportStatus
from api.barriers.models import Barrier, BarrierSearchCSVDownloadEvent
from api.barrier_reports.serializers import BarrierCsvExportSerializer
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket
from api.user.constants import USER_ACTIVITY_EVENT_TYPES
from api.user.models import UserActvitiyLog


logger = logging.getLogger(__name__)


def get_s3_client_and_bucket_name():
    bucket_id = "default"
    return get_s3_client_for_bucket(bucket_id), get_bucket_name(bucket_id)


def serializer_to_csv_bytes(serializer, field_names) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        extrasaction="ignore",
        fieldnames=field_names.keys(),
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerow(field_names)
    for row in serializer.data:
        writer.writerow(_transform_csv_row(row))
    content = output.getvalue().encode('utf-8')
    return content


def create_barrier_report(user, barrier_ids) -> BarrierReport:
    filename = f"csv/{user.id}/Data_Hub_Market_Access_Barriers_{now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"

    UserActvitiyLog.objects.create(
        user=user,
        event_type=USER_ACTIVITY_EVENT_TYPES.BARRIER_CSV_DOWNLOAD,
        event_description="User has exported a CSV of barriers",
    )

    barrier_report = BarrierReport.objects.create(
        user=user, status=BarrierReportStatus.PENDING, filename=filename
    )

    # Make celery call don't wait for return
    # from api.barrier_reports.tasks import generate_s3_and_send_email
    tasks.generate_barrier_report_file.delay(
        barrier_report.id,
        barrier_ids,
    )

    return barrier_report


def generate_barrier_report_file(
    barrier_report_id: str,
    barrier_ids: List[str],
) -> None:
    logger.info(f'Generating report for BarrierReport: {barrier_report_id}')
    try:
        barrier_report = BarrierReport.objects.select_related('user').get(id=barrier_report_id)
    except BarrierReport.DoesNotExist:
        raise BarrierReportDoesNotExist(barrier_report_id)

    barrier_report.processing()

    queryset = Barrier.objects.filter(id__in=barrier_ids)
    serializer = BarrierCsvExportSerializer(queryset, many=True)

    # Save the download event in the database
    BarrierSearchCSVDownloadEvent.objects.create(
        email=barrier_report.user.email,
        barrier_ids=",".join(barrier_ids),
    )

    csv_bytes = serializer_to_csv_bytes(serializer, BARRIER_FIELD_TO_REPORT_TITLE)
    s3_client, bucket = get_s3_client_and_bucket_name()

    # Upload file
    s3_client.put_object(
        Bucket=bucket,
        Body=csv_bytes,
        Key=barrier_report.filename
    )

    barrier_report.complete()

    # Notify user task is complete
    tasks.barrier_report_complete_notification.delay(barrier_report_id=str(barrier_report.id))


def get_presigned_url(barrier_report):
    s3_client, bucket = get_s3_client_and_bucket_name()

    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": barrier_report.filename},
    )


def barrier_report_complete_notification(barrier_report_id: str):
    """
    Send notification to user with a presigned url that a Barrier Report has been completed.
    """
    logger.info(f'Notifying user for BarrierReport: {barrier_report_id}')
    try:
        barrier_report = BarrierReport.objects.select_related('user').get(id=barrier_report_id)
    except BarrierReport.DoesNotExist:
        raise BarrierReportDoesNotExist(barrier_report_id)

    if barrier_report.status != BarrierReportStatus.COMPLETE:
        raise BarrierReportNotificationError("Barrier status not Complete")

    presigned_url = get_presigned_url(barrier_report)

    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    client.send_email_notification(
        email_address=barrier_report.user.email,
        template_id=settings.NOTIFY_GENERATED_FILE_ID,
        personalisation={
            "first_name": barrier_report.user.first_name.capitalize(),
            "file_name": barrier_report.filename,
            "file_url": presigned_url,
        },
    )
