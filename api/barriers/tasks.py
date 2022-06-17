import csv
import logging
from csv import DictWriter
from datetime import timedelta
from tempfile import NamedTemporaryFile
from typing import Dict, List

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.csv import _transform_csv_row
from api.barriers.models import Barrier, BarrierSearchCSVDownloadEvent
from api.barriers.serializers import BarrierCsvExportSerializer
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket
from api.metadata.constants import BarrierStatus

logger = logging.getLogger(__name__)


def upload_to_s3(filename: str, key: str) -> str:
    bucket_id = "default"
    bucket_name = get_bucket_name(bucket_id)
    s3_client = get_s3_client_for_bucket(bucket_id)
    s3_client.upload_file(filename, bucket_name, key)
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
    )


def write_to_temporary_file(
    temporary_file: NamedTemporaryFile,
    field_titles: Dict[str, str],
    serializer: BarrierCsvExportSerializer,
):
    writer = DictWriter(
        temporary_file,
        extrasaction="ignore",
        fieldnames=field_titles.keys(),
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writerow(field_titles)
    for row in serializer.data:
        writer.writerow(_transform_csv_row(row))
    temporary_file.flush()


def create_named_temporary_file():
    return NamedTemporaryFile(mode="w+t", encoding="utf-8-sig")


def generate_and_upload_to_s3(
    s3_filename: str,
    field_titles: Dict[str, str],
    serializer: BarrierCsvExportSerializer,
) -> str:
    with create_named_temporary_file() as tf:
        write_to_temporary_file(tf, field_titles, serializer)
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
def auto_update_inactive_barrier_status():
    """
    Take a list of barriers with modifed_on dates older than X months and X months
    for each barrier, update their status to "Dormant" and "Archived" respectively
    """

    archive_inactivity_threshold_date = timezone.now() - timedelta(
        days=settings.BARRIER_INACTIVITY_ARCHIVE_THRESHOLD_DAYS
    )
    # We only want to automatically archive barriers which are dormant
    barriers_to_be_archived = Barrier.objects.filter(
        modified_on__lt=archive_inactivity_threshold_date,
        status__exact=5,
    )
    for barrier in barriers_to_be_archived:
        # Can't use the barrier archive function, as there is no User performing the action
        Barrier.objects.filter(id=barrier.id).update(
            status=BarrierStatus.ARCHIVED,
            archived=True,
            archived_reason="Other",
            archived_explanation="Barrier has been inactive longer than the threshold for archival.",
        )

    dormant_inactivity_threshold_date = timezone.now() - timedelta(
        days=settings.BARRIER_INACTIVITY_DORMANT_THRESHOLD_DAYS
    )
    # We don't want to change resolved or already archived/dormant barriers
    barriers_to_be_dormant = Barrier.objects.filter(
        modified_on__lt=dormant_inactivity_threshold_date,
        status__in=[0, 1, 2, 7],
    )
    for barrier in barriers_to_be_dormant:
        # Use save function rather than update so countdown to auto-archival starts now
        barrier.status = BarrierStatus.DORMANT
        barrier.save()


@shared_task
def send_barrier_inactivity_reminders():
    """
    Get list of all barriers with modified_on and activity_reminder_sent dates older than 6 months
    For each barrier sent a reminder notification to the barrier owner
    """

    # datetime 6 months ago
    inactivity_threshold_date = timezone.now() - timedelta(
        days=settings.BARRIER_INACTIVITY_THRESHOLD_DAYS
    )
    repeat_reminder_threshold_date = timezone.now() - timedelta(
        days=settings.BARRIER_REPEAT_REMINDER_THRESHOLD_DAYS
    )

    barriers_needing_reminder = Barrier.objects.filter(
        modified_on__lt=inactivity_threshold_date
    ).filter(
        Q(activity_reminder_sent__isnull=True)
        | Q(activity_reminder_sent__lt=repeat_reminder_threshold_date)
    )

    for barrier in barriers_needing_reminder:
        recipient = barrier.barrier_team.filter(role="Owner").first()
        if not recipient:
            recipient = barrier.barrier_team.filter(role="Reporter").first()
        if not recipient:
            logger.warn(f"No recipient found for barrier {barrier.id}")
            continue
        if not recipient.user:
            logger.warn(
                f"No user found for recipient {recipient.id} and barrier {barrier.id}"
            )
            continue

        recipient = recipient.user

        full_name = f"{recipient.first_name} {recipient.last_name}"

        client = NotificationsAPIClient(settings.NOTIFY_API_KEY)

        client.send_email_notification(
            email_address=recipient.email,
            template_id=settings.BARRIER_INACTIVITY_REMINDER_NOTIFICATION_ID,
            personalisation={
                "barrier_title": barrier.title,
                "barrier_url": f"{settings.DMAS_BASE_URL}/barriers/{barrier.id}/",
                "full_name": full_name,
                "barrier_created_date": barrier.created_on.strftime("%d %B %Y"),
            },
        )
        barrier.activity_reminder_sent = timezone.now()
        barrier.save()
