import calendar
import csv
import logging
from csv import DictWriter
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from typing import Dict, List

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.template.defaultfilters import pluralize
from django.utils import timezone
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.csv import _transform_csv_row
from api.barriers.models import Barrier, BarrierSearchCSVDownloadEvent
from api.barriers.serializers import BarrierCsvExportSerializer
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket
from api.metadata.constants import (
    REGIONS_WITH_LEADS,
    TRADING_BLOCS,
    WIDER_EUROPE_REGIONS,
    BarrierStatus,
)
from api.metadata.utils import get_country

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


def get_inactivty_threshold_dates():

    inactivity_threshold_dates = {}

    current_date = timezone.now()
    last_day_of_month = calendar.monthrange(current_date.year, current_date.month)[1]
    target_date = current_date.replace(day=last_day_of_month)

    inactivity_threshold_dates[
        "archive_inactivity_threshold_date"
    ] = target_date - timedelta(days=settings.BARRIER_INACTIVITY_ARCHIVE_THRESHOLD_DAYS)
    inactivity_threshold_dates[
        "dormant_inactivity_threshold_date"
    ] = target_date - timedelta(days=settings.BARRIER_INACTIVITY_DORMANT_THRESHOLD_DAYS)
    inactivity_threshold_dates["inactivity_threshold_date"] = current_date - timedelta(
        days=settings.BARRIER_INACTIVITY_THRESHOLD_DAYS
    )
    inactivity_threshold_dates[
        "repeat_reminder_threshold_date"
    ] = current_date - timedelta(days=settings.BARRIER_REPEAT_REMINDER_THRESHOLD_DAYS)

    return inactivity_threshold_dates


def get_barriers_to_update_this_month():

    barriers_to_update = {}

    threshold_dates = get_inactivty_threshold_dates()

    # We only want to automatically archive barriers which are dormant
    barriers_to_update["barriers_to_be_archived"] = Barrier.objects.filter(
        modified_on__lt=threshold_dates["archive_inactivity_threshold_date"],
        status__exact=5,
        archived=False,
    )

    # We don't want to change resolved or already archived/dormant barriers
    barriers_to_update["barriers_to_be_dormant"] = Barrier.objects.filter(
        modified_on__lt=threshold_dates["dormant_inactivity_threshold_date"],
        status__in=[1, 2, 7],
        archived=False,
    )

    return barriers_to_update


def get_barriers_overseas_region(country_id, trading_bloc):

    # Get the overseas region of the barrier
    if country_id:
        # Details stored in country metadata, not the barrier itself
        country_details = get_country(str(country_id))

        # Special case for empty "overseas_region" - internal barriers for the UK go to the Europe regional lead
        if not country_details["overseas_region"]:
            overseas_region = "Europe"
        # Special case for wider europe countries - metadata has them in with the rest of europe
        elif country_details["name"] in WIDER_EUROPE_REGIONS:
            overseas_region = "Wider Europe"
        # All other countries map to their API given region
        else:
            overseas_region = country_details["overseas_region"]["name"]

    else:
        # Details stored in trading bloc constant, not the barrier itself
        trading_bloc_details = TRADING_BLOCS.get(trading_bloc)
        overseas_region = trading_bloc_details["regional_name"]

    return overseas_region


def get_auto_update_barrier_status_markdown(barriers, status_to_update):
    """
    Generate gov notify style markdown for the barriers which will be automatically updated.
    The template syntax does not allow loops, so we have to generate the markdown here.
    """
    # Heading - "Archived" or "Dormant"
    markdown = ""
    markdown += f"#{status_to_update}"

    # Sub-heading - Indicates how many barriers will be actioned
    barrier_count = len(barriers)
    action_suffix = "archived"
    if status_to_update == "Dormant":
        action_suffix = "made dormant"

    if barrier_count:
        markdown += f"\n{barrier_count} barrier{pluralize(barrier_count)} will be {action_suffix}\n"
    else:
        markdown += f"\nNo barriers will be {action_suffix} in your region this month\n"

    # List - bullet point list of barriers to be actioned
    for barrier in barriers:
        markdown += f"\n* {barrier.title}\n"
        markdown += f"{settings.DMAS_BASE_URL}/barriers/{barrier.code}?en=n\n"
        markdown += "\n---\n"

    return markdown


@shared_task
def auto_update_inactive_barrier_status():
    """
    Take a list of barriers with modifed_on dates older than X months and X months
    for each barrier, update their status to "Dormant" and "Archived" respectively
    """

    barriers_to_update = get_barriers_to_update_this_month()

    for barrier in barriers_to_update["barriers_to_be_archived"]:
        # Can't use the barrier archive function, as there is no User performing the action
        Barrier.objects.filter(id=barrier.id).update(
            status=BarrierStatus.ARCHIVED,
            archived=True,
            archived_reason="Other",
            archived_explanation="Barrier has been inactive longer than the threshold for archival.",
            archived_on=datetime.today(),
        )

    for barrier in barriers_to_update["barriers_to_be_dormant"]:
        # Use save function rather than update so countdown to auto-archival starts now
        barrier.status = BarrierStatus.DORMANT
        barrier.save()


@shared_task
def send_auto_update_inactive_barrier_notification():
    """
    Get a list of barriers that will, in the next month, pass the threshold for automatic
    status change to dormancy and archival. Send an email to relevant regional leads.
    """

    # Get the barriers that are scheduled for auto-updating this month
    barriers_to_update = get_barriers_to_update_this_month()

    # To be used in the email template - the date the barriers will be updated
    # This will be 15 days into the month.
    today = datetime.today()
    date_of_update = datetime(today.year, today.month, 15)
    date_of_update = date_of_update.strftime("%d-%m-%Y")

    # Get region constants
    regions = REGIONS_WITH_LEADS

    # Create dictionary lists for each region
    archive_notification_data = {}
    dormancy_notification_data = {}
    for region in regions:
        archive_notification_data[f"{region}"] = []
        dormancy_notification_data[f"{region}"] = []

    # Go through barrier lists, check the region for the barrier, then add to the specific
    # region's dictionary list
    for barrier in barriers_to_update["barriers_to_be_archived"]:
        overseas_region = get_barriers_overseas_region(
            barrier.country, barrier.trading_bloc
        )
        archive_notification_data[f"{overseas_region}"].append(barrier)

    for barrier in barriers_to_update["barriers_to_be_dormant"]:
        overseas_region = get_barriers_overseas_region(
            barrier.country, barrier.trading_bloc
        )
        dormancy_notification_data[f"{overseas_region}"].append(barrier)

    # Go through each region, get the list of users marked as that regions lead
    # use Notify API to send them the email notification, sending along the barriers
    # from both archive and dormant lists as content
    for region in regions:
        region_lead_user_group_name = regions[f"{region}"]
        mail_list = User.objects.filter(groups__name=region_lead_user_group_name)

        client = NotificationsAPIClient(settings.NOTIFY_API_KEY)

        for region_lead_user in mail_list:

            full_name = f"{region_lead_user.first_name} {region_lead_user.last_name}"

            # Barriers must be formatted correctly for the GOV markdown in the email template
            barriers_to_be_archived_formatted = get_auto_update_barrier_status_markdown(
                archive_notification_data[f"{region}"], "Archived"
            )
            barriers_to_be_dormant_formatted = get_auto_update_barrier_status_markdown(
                dormancy_notification_data[f"{region}"], "Dormant"
            )

            client.send_email_notification(
                email_address=region_lead_user.email,
                template_id=settings.AUTOMATIC_ARCHIVE_AND_DORMANCY_UPDATE_EMAIL_TEMPLATE_ID,
                personalisation={
                    "full_name": full_name,
                    "date_for_update": date_of_update,
                    "barriers_to_be_archived": barriers_to_be_archived_formatted,
                    "barriers_to_be_dormant": barriers_to_be_dormant_formatted,
                },
            )


@shared_task
def send_barrier_inactivity_reminders():
    """
    Get list of all barriers with modified_on and activity_reminder_sent dates older than 6 months
    For each barrier sent a reminder notification to the barrier owner
    """

    threshold_dates = get_inactivty_threshold_dates()

    barriers_needing_reminder = Barrier.objects.filter(
        modified_on__lt=threshold_dates["inactivity_threshold_date"]
    ).filter(
        Q(activity_reminder_sent__isnull=True)
        | Q(
            activity_reminder_sent__lt=threshold_dates["repeat_reminder_threshold_date"]
        )
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
