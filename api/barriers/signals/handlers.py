from django.dispatch import receiver

from api.barriers.models import HistoricalBarrierInstance, HistoricalPublicBarrier
from api.barriers.history.all import HistoryItemFactory
from api.history.models import CachedHistoryItem

from simple_history.signals import post_create_historical_record


def barrier_categories_changed(sender, instance, action, **kwargs):
    """
    Triggered when barriers.categories (m2m field) is changed

    Ensure the historical record saves a copy of the categories.

    post_remove and post_add can both get called, but we only want to create one
    history record, so we need to check if one has already been created
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "categories_history_saved"):
            historical_instance = HistoricalBarrierInstance.objects.filter(
                id=instance.pk
            ).latest()
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
            historical_instance = HistoricalBarrierInstance.objects.filter(
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


@receiver(post_create_historical_record)
def post_create_historical_record(sender, history_instance, **kwargs):
    items = HistoryItemFactory.create_history_items(
        new_record=history_instance,
        old_record=history_instance.prev_record,
    )

    for item in items:
        CachedHistoryItem.create_from_history_item(item)
