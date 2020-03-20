from django.apps import AppConfig


class AssessmentConfig(AppConfig):
    name = "api.assessment"

    def ready(self):
        from django.db.models.signals import m2m_changed
        from .models import Assessment
        from .signals.handlers import assessment_documents_changed

        m2m_changed.connect(
            assessment_documents_changed,
            sender=Assessment.documents.through
        )
