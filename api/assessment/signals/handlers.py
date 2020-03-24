from api.assessment.models import HistoricalAssessment


def assessment_documents_changed(sender, instance, action, **kwargs):
    """
    Triggered when assessment.documents (m2m field) is changed

    Ensure the historical record saves a copy of the documents.
    """
    if action in ("post_add", "post_remove"):
        instance.save()
        historical_instance = HistoricalAssessment.objects.filter(id=instance.pk).latest()
        historical_instance.documents_cache = [
            {
                "id": str(document["id"]),
                "name": document["original_filename"],
            } for document in instance.documents.values("id", "original_filename")
        ]
        historical_instance.save()
