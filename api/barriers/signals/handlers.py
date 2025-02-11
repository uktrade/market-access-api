import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.models import Barrier, HistoricalBarrier, HistoricalPublicBarrier
from api.barriers.tasks import (
    send_new_valuation_notification,
    send_top_priority_notification,
)
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS
from api.related_barriers.manager import BARRIER_UPDATE_FIELDS
from api.related_barriers.tasks import update_related_barrier

logger = logging.getLogger(__name__)


def barrier_categories_changed(sender, instance, action, **kwargs):
    """
    Triggered when barriers.categories (m2m field) is changed

    Ensure the historical record saves a copy of the categories.

    post_remove and post_add can both get called, but we only want to create one
    history record, so we need to check if one has already been created
    """

    if action in ("post_add", "post_remove"):
        with transaction.atomic():
            if hasattr(instance, "categories_history_saved"):
                historical_instance = HistoricalBarrier.objects.filter(
                    id=instance.pk
                ).latest("history_date")
                historical_instance.update_categories()
                historical_instance.save()
            else:
                instance.categories_history_saved = True
                instance.save()


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


def barrier_policy_teams_changed(sender, instance, action, **kwargs):
    """
    Triggered when barriers.policy_teams (m2m field) is changed
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "policy_teams_history_saved"):
            historical_instance = HistoricalBarrier.objects.filter(
                id=instance.pk
            ).latest()
            historical_instance.update_policy_teams()
            historical_instance.save()
        else:
            instance.policy_teams_history_saved = True
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
                send_new_valuation_notification.delay(instance.id)
    else:
        if created:
            # Get the barrier and pass to the notification function
            send_new_valuation_notification.delay(instance.barrier_id)


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
                send_top_priority_notification.delay("APPROVAL", instance.id)
            elif (
                new_top_priority_status == "NONE"
                and old_top_priority_status == "APPROVAL_PENDING"
            ):
                # Removal of APPROVAL_PENDING status can be in 2 situations;
                # - Admin has rejected, so send email
                # - Barrier has moved to WATCHLIST priority, automatically removing the request, so don't send email

                # If the barrier's priority is WATCHLIST now, we know this shouldn't trigger an email
                if instance.priority_level == "WATCHLIST":
                    return
                else:
                    send_top_priority_notification.delay("REJECTION", instance.id)
            else:
                # Status change indicates barrier has neither been rejected or accepted in this save operation
                return
        else:
            # Return if there has been no change in top_priority_status
            return


@transaction.atomic
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


@transaction.atomic
def related_barrier_update_embeddings(sender, instance, *args, **kwargs):
    logger.info(
        f"(Handler) Running related_barrier_update_embeddings() handler for {instance.pk}"
    )
    try:
        current_barrier_object = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        logger.info(f"No Barrier found: {instance.pk}")
        return

    changed = any(
        getattr(current_barrier_object, field) != getattr(instance, field)
        for field in BARRIER_UPDATE_FIELDS
    )
    logger.info(
        f"(Handler) Updating related barrier embeddings for {instance.pk}: {changed}"
    )

    if changed and not current_barrier_object.draft:
        update_related_barrier(barrier_id=str(instance.pk))
