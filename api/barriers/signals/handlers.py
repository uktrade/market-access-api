import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications_python_client.notifications import NotificationsAPIClient
from simple_history.signals import post_create_historical_record

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.models import (
    Barrier,
    BarrierRequestDownloadApproval,
    HistoricalBarrier,
    HistoricalPublicBarrier,
    PublicBarrier,
    PublicBarrierLightTouchReviews,
)
from api.history.factories import HistoryItemFactory
from api.history.models import CachedHistoryItem
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS

logger = logging.getLogger(__name__)


def barrier_categories_changed(sender, instance, action, **kwargs):
    """
    Triggered when barriers.categories (m2m field) is changed

    Ensure the historical record saves a copy of the categories.

    post_remove and post_add can both get called, but we only want to create one
    history record, so we need to check if one has already been created
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "categories_history_saved"):
            historical_instance = HistoricalBarrier.objects.filter(
                id=instance.pk
            ).latest("history_date")
            historical_instance.update_categories()
            historical_instance.save()
        else:
            instance.categories_history_saved = True
            instance.save()


def barrier_organisations_changed(sender, instance, action, **kwargs):

    if action in ("post_add", "post_remove"):
        instance.public_barrier.light_touch_reviews.save()


def barrier_tags_changed(sender, instance, action, **kwargs):
    """
    Triggered when barriers.tags (m2m field) is changed
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "tags_history_saved"):
            historical_instance = HistoricalBarrier.objects.filter(
                id=instance.pk
            ).latest()
            historical_instance.update_tags()
            historical_instance.save()
        else:
            instance.tags_history_saved = True
            instance.save()


def public_barrier_categories_changed(sender, instance, action, **kwargs):
    """
    Triggered when PublicBarrier.categories (m2m field) is changed

    Ensure the historical record saves a copy of the categories.

    post_remove and post_add can both get called, but we only want to create one
    history record, so we need to check if one has already been created
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "categories_history_saved"):
            historical_instance = HistoricalPublicBarrier.objects.filter(
                id=instance.pk
            ).latest()
            historical_instance.update_categories()
            historical_instance.save()
        else:
            instance.categories_history_saved = True
            instance.save()


def public_barrier_light_touch_reviews_changed(
    sender, instance: PublicBarrierLightTouchReviews, **kwargs
):
    if hasattr(instance, "light_touch_reviews_history_saved"):
        historical_instance = HistoricalPublicBarrier.objects.filter(
            id=instance.public_barrier.id
        ).latest()
        historical_instance.update_light_touch_reviews()
        historical_instance.save()
    else:
        instance.light_touch_reviews_history_saved = True
        instance.public_barrier.save()


def public_barrier_content_update(
    sender, instance: PublicBarrier, update_fields, **kwargs
):
    """
    When public barrier summary or title is changed remove content team approval and
    flag that content has changed since last approval
    """
    pb_filter = PublicBarrier.objects.filter(id=instance.id)
    if not pb_filter.exists():
        return
    previous_instance = pb_filter.first()

    has_public_content_changed = (instance.title != previous_instance.title) or (
        instance.summary != previous_instance.summary
    )

    if not has_public_content_changed:
        return

    try:
        light_touch_reviews: PublicBarrierLightTouchReviews = (
            instance.light_touch_reviews
        )
    except PublicBarrier.light_touch_reviews.RelatedObjectDoesNotExist:
        light_touch_reviews = PublicBarrierLightTouchReviews.objects.create(
            public_barrier=instance
        )
    if not light_touch_reviews.content_team_approval:
        return

    light_touch_reviews.content_team_approval = False
    light_touch_reviews.has_content_changed_since_approval = True
    light_touch_reviews.save()


def barrier_completion_percentage_changed(sender, instance: Barrier, **kwargs):
    """
    After a barrier is updated, re-calculate its completion percentage.
    """
    edited_barrier = Barrier.objects.get(id=instance.id)

    new_percentage = 0

    if edited_barrier.location:
        new_percentage += 18
    if edited_barrier.summary:
        new_percentage += 18
    if edited_barrier.source:
        new_percentage += 16
    if edited_barrier.sectors:
        new_percentage += 16
    if edited_barrier.categories.all().count() > 0:
        new_percentage += 16
    if edited_barrier.commodities.all().count() > 0:
        new_percentage += 16

    # IMPORTANT - Use Update here instead of save or we'll get stuck in
    # an endless loop where post_save keeps getting called!!!
    Barrier.objects.filter(id=instance.id).update(completion_percent=new_percentage)


@receiver(post_save, sender=Barrier)
@receiver(post_save, sender=EconomicAssessment)
@receiver(post_save, sender=EconomicImpactAssessment)
@receiver(post_save, sender=ResolvabilityAssessment)
@receiver(post_save, sender=StrategicAssessment)
def barrier_new_valuation_email_notification(sender, instance, created, **kwargs):
    """
    When a new assessment has been added, send an email notification to owner & contributors
    Assessments are their own objects, so can listen for new ones created except Commercial
    Value Assessment, which is recorded on the barrier iteslf.
    """
    if isinstance(instance, Barrier):
        # Check if Commercial Value columns have changed value
        previous_instances = HistoricalBarrier.objects.filter(id=instance.pk)
        if previous_instances.count() > 1:
            last_instance = previous_instances[1]
            old_commercial_value = last_instance.commercial_value
            new_commercial_value = instance.commercial_value
            old_commercial_value_explanation = (
                last_instance.commercial_value_explanation
            )
            new_commercial_value_explanation = instance.commercial_value_explanation
            if (old_commercial_value != new_commercial_value) | (
                old_commercial_value_explanation != new_commercial_value_explanation
            ):
                send_new_valuation_notification(instance)
    else:
        if created:
            # Get the barrier and pass to the notification function
            barrier = Barrier.objects.filter(id=instance.barrier_id).first()
            send_new_valuation_notification(barrier)


def send_new_valuation_notification(barrier):
    """
    Create the email client and send the new valuation notification email
    """
    template_id = settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID

    barrier_team_list = barrier.barrier_team.all()
    for team_recipient in barrier_team_list:
        if team_recipient.role in ["Owner", "Contributor"]:
            recipient = team_recipient.user

            personalisation_items = {}
            personalisation_items["first_name"] = recipient.first_name
            personalisation_items["barrier_id"] = str(barrier.id)
            personalisation_items["barrier_code"] = str(barrier.code)

            client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
            client.send_email_notification(
                email_address=recipient.email,
                template_id=template_id,
                personalisation=personalisation_items,
            )


def barrier_priority_approval_email_notification(sender, instance: Barrier, **kwargs):
    """
    If a barrier's top_priority_status has changed, check if a
    notification email needs to be sent, then call the function to send it.
    """

    # The operation is post-save to ensure operation completed successfully before
    # notification so we need the second latest historical barrier object,
    # or we would be comparing the new instance to itself.
    previous_instances = HistoricalBarrier.objects.filter(id=instance.pk)

    if previous_instances.count() > 1:
        last_instance = previous_instances[1]

        old_top_priority_status = last_instance.top_priority_status
        new_top_priority_status = instance.top_priority_status

        if new_top_priority_status != old_top_priority_status:
            if new_top_priority_status == "APPROVED":
                # If status has changed to APPROVED, no matter what it was, it has now been approved
                send_top_priority_notification("APPROVAL", instance)
            elif (
                new_top_priority_status == "NONE"
                and old_top_priority_status == "APPROVAL_PENDING"
            ):
                # If status has changed from Pending to None, we know it has been rejected
                send_top_priority_notification("REJECTION", instance)
            else:
                # Status change indicates barrier has neither been rejected or accepted in this save operation
                return
        else:
            # Return if there has been no change in top_priority_status
            return


def send_top_priority_notification(email_type, barrier):
    """
    Create the email client and send the top_priority notification email
    """

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


@receiver(post_create_historical_record)
def post_create_historical_record(sender, history_instance, **kwargs):
    history_instance.refresh_from_db()
    items = HistoryItemFactory.create_history_items(
        new_record=history_instance,
        old_record=history_instance.prev_record,
    )

    for item in items:
        CachedHistoryItem.create_from_history_item(item)


@receiver(post_save, sender=BarrierRequestDownloadApproval)
def send_barrier_download_request_notification(sender, instance, created, **kwargs):
    if created:
        instance.send_notification()


def barrier_completion_top_priority_barrier_resolved(
    sender, instance: Barrier, **kwargs
):
    """
    After a barrier is updated, check if it has a status of 'Resolved: In Full' and has an
    APPROVED top_pritority status. If it does, change top_priority_status to RESOLVED.
    """
    edited_barrier = Barrier.objects.get(id=instance.id)

    if (
        edited_barrier.status == 4
        and edited_barrier.top_priority_status == TOP_PRIORITY_BARRIER_STATUS.APPROVED
    ):
        # IMPORTANT - Use Update here instead of save or we'll get stuck in
        # an endless loop where post_save keeps getting called!!!
        Barrier.objects.filter(id=instance.id).update(
            top_priority_status=TOP_PRIORITY_BARRIER_STATUS.RESOLVED
        )
