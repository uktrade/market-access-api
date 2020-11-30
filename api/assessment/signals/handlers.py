from api.assessment.models import HistoricalEconomicAssessment


def assessment_documents_changed(sender, instance, action, **kwargs):
    """
    Triggered when assessment.documents (m2m field) is changed

    Ensure the historical record saves a copy of the documents.
    """

    if action in ("post_add", "post_remove"):
        if hasattr(instance, "documents_history_saved"):
            historical_instance = HistoricalEconomicAssessment.objects.filter(
                id=instance.pk
            ).latest()
            historical_instance.update_documents()
            historical_instance.save()
        else:
            instance.documents_history_saved = True
            instance.save()
