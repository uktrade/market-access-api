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
from api.barriers.helpers import get_or_create_public_barrier
from api.barriers.models import (
    Barrier,
    BarrierRequestDownloadApproval,
    HistoricalBarrier,
    HistoricalPublicBarrier,
    PublicBarrier,
    PublicBarrierLightTouchReviews,
)
from api.barriers.signals.tasks import (
    send_new_valuation_notification,
    send_top_priority_notification,
)
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS
from api.related_barriers import manager
from api.related_barriers.constants import BarrierEntry
from api.related_barriers.manager import BARRIER_UPDATE_FIELDS

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

            public_barrier, _ = get_or_create_public_barrier(barrier=instance)

            if (
                not public_barrier.changed_since_published
                and public_barrier.last_published_on
            ):
                public_barrier.changed_since_published = True
                public_barrier.save()


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

    with transaction.atomic():
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


@receiver(post_save, sender=BarrierRequestDownloadApproval)
def send_barrier_download_request_notification(sender, instance, created, **kwargs):
    if created:
        instance.send_notification()


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
def barrier_changed_after_published(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
        public_barrier, _ = get_or_create_public_barrier(barrier=instance)
    except sender.DoesNotExist:
        pass  # Object is new, so field hasn't technically changed, but you may want to do something else here.
    else:
        if (
            not public_barrier.changed_since_published
            and public_barrier.last_published_on
        ):
            # Only set changed_since_published if certain barrier elements have been changed.
            if any(
                [
                    obj.status != instance.status,
                    str(obj.country) != str(instance.country),
                    obj.title != instance.title,
                    obj.categories != instance.categories,
                    obj.summary != instance.summary,
                    [str(s) for s in obj.sectors] != [str(s) for s in instance.sectors],
                ]
            ):
                public_barrier.changed_since_published = True
                public_barrier.save()


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
        if not manager.manager:
            manager.init()
        try:
            manager.manager.update_barrier(
                BarrierEntry(
                    id=str(current_barrier_object.id),
                    barrier_corpus=manager.barrier_to_corpus(current_barrier_object),
                )
            )
        except Exception as e:
            # We don't want barrier embedding updates to break worker so just log error
            logger.critical(str(e))
