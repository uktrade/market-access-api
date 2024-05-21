import logging

from celery import shared_task
from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient

logger = logging.getLogger(__name__)


@shared_task
def send_new_valuation_notification(barrier_id: int):
    """
    Create the email client and send the new valuation notification email
    """

    # avoid circular import
    from api.barriers.models import Barrier

    barrier = Barrier.objects.get(id=barrier_id)
    template_id = settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID

    barrier_team_list = barrier.barrier_team.all()
    for team_recipient in barrier_team_list:
        if team_recipient.role in ["Owner", "Contributor"]:
            recipient = team_recipient.user

            personalisation_items = {}
            try:
                personalisation_items["first_name"] = recipient.first_name
            except AttributeError:
                logger.warning("User has no first_name attribute")
                continue
            personalisation_items["barrier_id"] = str(barrier.id)
            personalisation_items["barrier_code"] = str(barrier.code)

            client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
            client.send_email_notification(
                email_address=recipient.email,
                template_id=template_id,
                personalisation=personalisation_items,
            )
            # log the email sent
            logger.info(f"Email sent to {recipient.email} for barrier {barrier.id}")


@shared_task
def send_top_priority_notification(email_type: str, barrier_id: int):
    """
    Create the email client and send the top_priority notification email
    """

    # avoid circular import
    from api.barriers.models import Barrier

    barrier = Barrier.objects.get(id=barrier_id)

    # Choose accepted or rejected template
    template_id = ""
    if email_type == "APPROVAL":
        template_id = settings.BARRIER_PB100_ACCEPTED_EMAIL_TEMPLATE_ID
    elif email_type == "REJECTION":
        template_id = settings.BARRIER_PB100_REJECTED_EMAIL_TEMPLATE_ID

    personalisation_items = {}

    # Get barrier owner
    recipient = barrier.barrier_team.filter(role="Owner").first()
    if not recipient:
        logger.warning(f"Barrier {barrier.id} has no owner")
        return

    recipient = recipient.user
    personalisation_items["first_name"] = recipient.first_name

    # Seperate the barrier ID
    personalisation_items["barrier_id"] = str(barrier.code)

    # Build URL to the barrier
    personalisation_items[
        "barrier_url"
    ] = f"{settings.DMAS_BASE_URL}/barriers/{barrier.id}/"

    # If its a rejection, we need to also get the reason for rejection
    if email_type == "REJECTION":
        personalisation_items[
            "decision_reason"
        ] = barrier.top_priority_rejection_summary

    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    client.send_email_notification(
        email_address=recipient.email,
        template_id=template_id,
        personalisation=personalisation_items,
    )
    # log the email sent
    logger.info(f"Email sent to {recipient.email} for barrier {barrier.id}")
