from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    name = "api.interactions"

    def ready(self):
        from django.db.models.signals import m2m_changed

        from .models import Interaction
        from .signals.handlers import interaction_documents_changed

        m2m_changed.connect(
            interaction_documents_changed, sender=Interaction.documents.through
        )
