from api.barriers.models import HistoricalBarrierInstance


def barrier_categories_changed(sender, instance, action, **kwargs):
    """
    Triggered when barriers.categories (m2m field) is changed

    Ensure the historical record saves a copy of the categories.
    """
    if action in ("post_add", "post_remove"):
        historical_instance = HistoricalBarrierInstance.objects.filter(id=instance.pk).latest()
        historical_instance.categories_cache = list(
            instance.categories.values_list("id", flat=True)
        )
        historical_instance.save()
