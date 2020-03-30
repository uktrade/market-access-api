from api.interactions.models import HistoricalInteraction


def interaction_documents_changed(sender, instance, action, **kwargs):
    """
    Triggered when interaction.documents (m2m field) is changed

    Ensure the historical record saves a copy of the documents.
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "documents_history_saved"):
            historical_instance = HistoricalInteraction.objects.filter(
                id=instance.pk
            ).latest()
            historical_instance.update_documents()
            historical_instance.save()
        else:
            instance.documents_history_saved = True
            instance.save()
