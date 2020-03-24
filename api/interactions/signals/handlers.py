from api.interactions.models import HistoricalInteraction


def interaction_documents_changed(sender, instance, action, **kwargs):
    """
    Triggered when interaction.documents (m2m field) is changed

    Ensure the historical record saves a copy of the documents.
    """
    if action in ("post_add", "post_remove"):
        instance.save()
        historical_instance = HistoricalInteraction.objects.filter(id=instance.pk).latest()
        historical_instance.documents_cache = [
            {
                "id": str(document["id"]),
                "name": document["original_filename"],
            } for document in instance.documents.values("id", "original_filename")
        ]
        historical_instance.save()
