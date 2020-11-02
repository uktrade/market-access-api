from django.apps import AppConfig


class BarriersConfig(AppConfig):
    name = "api.barriers"

    def ready(self):
        from django.db.models.signals import m2m_changed
        from .models import Barrier, PublicBarrier
        from .signals.handlers import (
            barrier_categories_changed,
            barrier_tags_changed,
            public_barrier_categories_changed,
        )

        m2m_changed.connect(
            barrier_categories_changed,
            sender=Barrier.categories.through
        )
        m2m_changed.connect(
            barrier_tags_changed,
            sender=Barrier.tags.through
        )
        m2m_changed.connect(
            public_barrier_categories_changed,
            sender=PublicBarrier.categories.through
        )
