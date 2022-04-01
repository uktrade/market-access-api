import csv
from csv import DictWriter
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from typing import Dict, List

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.csv import _transform_csv_row
from api.barriers.models import Barrier, BarrierSearchCSVDownloadEvent
from api.barriers.serializers import BarrierCsvExportSerializer
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket


def upload_to_s3(filename: str, key: str) -> str:
    bucket_id = "default"
    bucket_name = get_bucket_name(bucket_id)
    s3_client = get_s3_client_for_bucket(bucket_id)
    s3_client.upload_file(filename, bucket_name, key)
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
    )


def generate_and_upload_to_s3(
    s3_filename: str,
    field_titles: Dict[str, str],
    serializer: BarrierCsvExportSerializer,
) -> str:
    with NamedTemporaryFile(mode="w+t") as tf:
        writer = DictWriter(
            tf,
            extrasaction="ignore",
            fieldnames=field_titles.keys(),
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writerow(field_titles)
        for row in serializer.data:
            writer.writerow(_transform_csv_row(row))
        tf.flush()

        presigned_url = upload_to_s3(tf.name, s3_filename)

    return presigned_url


@shared_task
def generate_s3_and_send_email(
    barrier_ids: List[int],
    s3_filename: str,
    email: str,
    first_name: str,
    field_titles: Dict[str, str],
) -> None:
    queryset = Barrier.objects.filter(id__in=barrier_ids)
    serializer = BarrierCsvExportSerializer(queryset, many=True)

    # save the download event in the database
    BarrierSearchCSVDownloadEvent.objects.create(
        email=email,
        barrier_ids=",".join(barrier_ids),
    )

    presigned_url = generate_and_upload_to_s3(s3_filename, field_titles, serializer)
    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    client.send_email_notification(
        email_address=email,
        template_id=settings.NOTIFY_GENERATED_FILE_ID,
        personalisation={
            "first_name": first_name.capitalize(),
            "file_name": s3_filename,
            "file_url": presigned_url,
        },
    )


@shared_task
def send_barrier_inactivity_reminders():
    """
    Get list of all barriers with modified_on and activity_reminder_sent dates older than 6 months

    For each barrier sent a reminder notification to the barrier owner
    """

    # datetime 6 months ago
    inactivity_theshold_date = datetime.now() - timedelta(
        days=settings.BARRIER_INACTIVITY_THESHOLD_DAYS
    )
    repeat_reminder_theshold_date = datetime.now() - timedelta(
        days=settings.BARRIER_REPEAT_REMINDER_THESHOLD_DAYS
    )

    barriers_needing_reminder = Barrier.objects.filter(
        modified_on__lt=inactivity_theshold_date
    ).filter(
        Q(activity_reminder_sent__isnull=True)
        | Q(activity_reminder_sent__lt=repeat_reminder_theshold_date)
    )

    for barrier in barriers_needing_reminder:
        barrier_owner = barrier.barrier_team.get(role="Owner").user
        full_name = f"{barrier_owner.first_name} {barrier_owner.last_name}"

        client = NotificationsAPIClient(settings.NOTIFY_API_KEY)

        client.send_email_notification(
            email_address=barrier_owner.email,
            template_id=settings.BARRIER_INACTIVITY_REMINDER_NOTIFICATION_ID,
            personalisation={
                "barrier_title": barrier.title,
                "barrier_url": f"{settings.DMAS_BASE_URL}/barriers/{barrier.id}/",
                "full_name": full_name,
                "barrier_created_date": barrier.created_on.strftime("%d %B %Y"),
            },
        )
        barrier.activity_reminder_sent = datetime.now()
        barrier.save()
