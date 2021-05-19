from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from api.barriers.models import (
    HistoricalBarrier,
    HistoricalPublicBarrier,
    PublicBarrier,
    PublicBarrierLightTouchReviews,
)
from api.history.factories import HistoryItemFactory
from api.history.models import CachedHistoryItem


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


@receiver(post_create_historical_record)
def post_create_historical_record(sender, history_instance, **kwargs):
    history_instance.refresh_from_db()
    items = HistoryItemFactory.create_history_items(
        new_record=history_instance,
        old_record=history_instance.prev_record,
    )

    for item in items:
        CachedHistoryItem.create_from_history_item(item)
