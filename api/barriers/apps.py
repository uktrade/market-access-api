from django.apps import AppConfig


class BarriersConfig(AppConfig):
    name = "api.barriers"

    def ready(self):
        from django.db.models.signals import m2m_changed, post_save, pre_save

        from .models import Barrier
        from .signals.handlers import (
            barrier_categories_changed,
            barrier_completion_top_priority_barrier_resolved,
            barrier_priority_approval_email_notification,
            barrier_tags_changed,
            related_barrier_update_embeddings,
        )

        m2m_changed.connect(
            barrier_categories_changed, sender=Barrier.categories.through
        )
        m2m_changed.connect(barrier_tags_changed, sender=Barrier.tags.through)

        pre_save.connect(related_barrier_update_embeddings, sender=Barrier)

        post_save.connect(
            barrier_completion_top_priority_barrier_resolved, sender=Barrier
        )

        post_save.connect(barrier_priority_approval_email_notification, sender=Barrier)
