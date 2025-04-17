import logging
from typing import List

from django.conf import settings
from django.db.models import Prefetch, QuerySet
from django.utils.timezone import now
from notifications_python_client import NotificationsAPIClient

from api.barrier_downloads import tasks
from api.barrier_downloads.constants import BARRIER_FIELD_TO_COLUMN_TITLE
from api.barrier_downloads.exceptions import (
    BarrierDownloadDoesNotExist,
    BarrierDownloadNotificationError,
)
from api.barrier_downloads.models import BarrierDownload, BarrierDownloadStatus
from api.barrier_downloads.serializers import CsvDownloadSerializer
from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    BarrierSearchCSVDownloadEvent,
    EstimatedResolutionDateRequest,
    ProgrammeFundProgressUpdate,
)
from api.collaboration.models import TeamMember
from api.core.utils import serializer_to_csv_bytes
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket
from api.user.constants import USER_ACTIVITY_EVENT_TYPES
from api.user.models import UserActvitiyLog

logger = logging.getLogger(__name__)


def get_s3_client_and_bucket_name():
    bucket_id = "default"
    return get_s3_client_for_bucket(bucket_id), get_bucket_name(bucket_id)


def create_barrier_download(user, filters: dict, barrier_ids: List) -> BarrierDownload:
    filename = f"csv/{user.id}/DMAS_{now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
    default_name = filename.split("/")[2]

    UserActvitiyLog.objects.create(
        user=user,
        event_type=USER_ACTIVITY_EVENT_TYPES.BARRIER_CSV_DOWNLOAD,
        event_description="User has exported a CSV of barriers",
    )

    barrier_download = BarrierDownload.objects.create(
        created_by=user,
        status=BarrierDownloadStatus.PENDING,
        filters=filters,
        filename=filename,
        name=default_name,
        count=len(barrier_ids),
    )

    # Make celery call don't wait for return
    # from api.barrier_downloads.tasks import generate_s3_and_send_email
    tasks.generate_barrier_download_file.delay(
        barrier_download_id=barrier_download.id,
        barrier_ids=barrier_ids,
    )

    return barrier_download


def get_queryset(barrier_ids: List[str]) -> QuerySet:
    return (
        Barrier.objects.filter(id__in=barrier_ids)
        .select_related(
            "created_by",
        )
        .prefetch_related(
            "tags",
            Prefetch(
                "barrier_team",
                queryset=TeamMember.objects.select_related("user")
                .filter(role="Owner")
                .all(),
            ),
            "organisations",
            Prefetch(
                "progress_updates",
                queryset=BarrierProgressUpdate.objects.order_by("-created_on").all(),
            ),
            Prefetch(
                "programme_fund_progress_updates",
                queryset=ProgrammeFundProgressUpdate.objects.select_related(
                    "created_by"
                )
                .order_by("-created_on")
                .all(),
            ),
            "barrier_commodities",
            "public_barrier",
            "economic_assessments",
            "valuation_assessments",
            "policy_teams",
            Prefetch(
                "next_steps_items",
                queryset=BarrierNextStepItem.objects.filter(
                    status="IN_PROGRESS"
                ).order_by("-completion_date"),
            ),
            Prefetch(
                "estimated_resolution_date_request",
                queryset=EstimatedResolutionDateRequest.objects.filter(
                    status="NEEDS_REVIEW"
                ),
            ),
        )
        .only(
            "id",
            "code",
            "title",
            "is_summary_sensitive",
            "summary",
            "code",
            "status",
            "sub_status",
            "priority_level",
            "progress_updates",
            "country",
            "trading_bloc",
            "admin_areas",
            "sectors",
            "sectors_affected",
            "all_sectors",
            "product",
            "created_by",
            "reported_on",
            "status_date",
            "status_summary",
            "modified_on",
            "tags",
            "trade_direction",
            "top_priority_status",
            "next_steps_items",
            "estimated_resolution_date",
            "proposed_estimated_resolution_date",
            "public_barrier___public_view_status",
            "public_barrier__changed_since_published",
            "public_barrier___title",
            "public_barrier___summary",
            "commercial_value",
            "estimated_resolution_date_request",
        )
    )


def generate_barrier_download_file(
    barrier_download_id: str,
    barrier_ids: List[str],
) -> None:
    logger.info(f"Generating file for BarrierDownload: {barrier_download_id}")
    try:
        barrier_download = BarrierDownload.objects.select_related("created_by").get(
            id=barrier_download_id
        )
    except BarrierDownload.DoesNotExist:
        raise BarrierDownloadDoesNotExist(barrier_download_id)

    barrier_download.processing()

    qs = get_queryset(barrier_ids)
    serializer = CsvDownloadSerializer(qs, many=True)

    try:
        csv_bytes = serializer_to_csv_bytes(serializer, BARRIER_FIELD_TO_COLUMN_TITLE)
    except Exception:
        # Check for generic exceptions when creating csv file
        # Async task so no need to handle gracefully
        # Log error stack.
        logger.exception("Failed to create CSV")
        barrier_download.fail()
        raise

    s3_client, bucket = get_s3_client_and_bucket_name()

    # Upload file
    s3_client.put_object(Bucket=bucket, Body=csv_bytes, Key=barrier_download.filename)

    barrier_download.complete()

    # Save the download event in the database
    BarrierSearchCSVDownloadEvent.objects.create(
        email=barrier_download.created_by.email,
        barrier_ids=",".join(barrier_ids),
    )

    # Notify user task is complete
    tasks.barrier_download_complete_notification.delay(
        barrier_download_id=str(barrier_download.id)
    )


def delete_barrier_download(barrier_download: BarrierDownload):
    s3_client, bucket = get_s3_client_and_bucket_name()
    s3_client.delete_object(Bucket=bucket, Key=barrier_download.filename)
    barrier_download.delete()


def get_presigned_url(barrier_download):
    s3_client, bucket = get_s3_client_and_bucket_name()

    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": barrier_download.filename},
    )


def barrier_download_complete_notification(barrier_download_id: str):
    """
    Send notification to user with a presigned url that a Barrier Download has been completed.
    """
    logger.info(f"Notifying user for BarrierDownload: {barrier_download_id}")
    try:
        barrier_download = BarrierDownload.objects.select_related("created_by").get(
            id=barrier_download_id
        )
    except BarrierDownload.DoesNotExist:
        raise BarrierDownloadDoesNotExist(barrier_download_id)

    if barrier_download.status != BarrierDownloadStatus.COMPLETE:
        raise BarrierDownloadNotificationError("Barrier status not Complete")

    presigned_url = get_presigned_url(barrier_download)

    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    client.send_email_notification(
        email_address=barrier_download.created_by.email,
        template_id=settings.NOTIFY_GENERATED_FILE_ID,
        personalisation={
            "first_name": barrier_download.created_by.first_name.capitalize(),
            "file_name": barrier_download.filename,
            "file_url": presigned_url,
        },
    )
