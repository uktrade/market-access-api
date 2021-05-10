import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.defaultfilters import pluralize
from notifications_python_client.notifications import NotificationsAPIClient

from api.user.models import get_my_barriers_saved_search, get_team_barriers_saved_search

logger = logging.getLogger(__name__)


def get_saved_searches_markdown(saved_searches):
    """
    Generate gov notify style markdown for the saved searches.

    The template syntax does not allow loops, so we have to generate the markdown here.
    """
    markdown = ""

    for saved_search in saved_searches:
        markdown += f"#{saved_search.name}"

        if saved_search.notify_about_additions:
            new_count = saved_search.new_count_since_notified
            if new_count:
                markdown += f"\n{new_count} new barrier{pluralize(new_count)}\n"

            for barrier in saved_search.new_barriers_since_notified:
                markdown += f"\n* {barrier.title}\n"
                markdown += f"{settings.DMAS_BASE_URL}/barriers/{barrier.code}?en=n\n"

        if saved_search.notify_about_updates:
            updated_count = saved_search.updated_count_since_notified
            if updated_count:
                markdown += (
                    f"\n{updated_count} barrier{pluralize(updated_count)} updated\n"
                )

            for barrier in saved_search.updated_barriers_since_notified:
                markdown += f"\n* {barrier.title}\n"
                markdown += f"{settings.DMAS_BASE_URL}/barriers/{barrier.code}?en=u\n"

        markdown += "\n---\n"

    return markdown


def send_email(user, saved_searches):
    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    print("STUB: {user.values()}")
    logging.warning("STUB: {user.values()}")
    client.send_email_notification(
        email_address=user.email,
        template_id=settings.NOTIFY_SAVED_SEARCHES_TEMPLATE_ID,
        personalisation={
            "first_name": user.first_name,
            "saved_searches": get_saved_searches_markdown(saved_searches),
            "dashboard_link": settings.DMAS_BASE_URL,
        },
    )


def mark_user_saved_searches_as_notified(user):
    """
    Mark all of a user's saved searches as notified.

    We need to do this regardless of if the user has actually been notified, so that if
    they switch notifications on, we know what barriers were previously in the search.
    """
    my_barriers = get_my_barriers_saved_search(user)
    my_barriers.mark_as_notified()

    team_barriers = get_team_barriers_saved_search(user)
    team_barriers.mark_as_notified()

    for saved_search in user.saved_searches.all():
        saved_search.mark_as_notified()


def get_saved_searches_for_notification(user):
    """
    Get saved searches where there have been changes and user has asked to be notified.
    """
    my_barriers = get_my_barriers_saved_search(user)
    team_barriers = get_team_barriers_saved_search(user)

    saved_searches = []

    if my_barriers.should_notify():
        saved_searches.append(my_barriers)

    if team_barriers.should_notify():
        saved_searches.append(team_barriers)

    for saved_search in user.saved_searches.all():
        if saved_search.should_notify():
            saved_searches.append(saved_search)

    return saved_searches


@shared_task
def send_notification_emails():
    User = get_user_model()
    count = 0

    for user in User.objects.all():
        saved_searches = get_saved_searches_for_notification(user)
        if not saved_searches:
            continue

        logger.info(f"Sending saved search notification email to {user.email}")
        try:
            send_email(user, saved_searches)
            count += 1
        except Exception:
            logger.exception(f"Failed to send email to {user.email}")
        mark_user_saved_searches_as_notified(user)

    logger.info(f"{count} saved search notification emails sent")
