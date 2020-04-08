from django.apps import AppConfig


class BarriersConfig(AppConfig):
    name = "api.barriers"

    def ready(self):
        from django.db.models.signals import m2m_changed
        from .models import BarrierInstance
        from .signals.handlers import barrier_categories_changed, barrier_tags_changed

        m2m_changed.connect(
            barrier_categories_changed,
            sender=BarrierInstance.categories.through
        )
        m2m_changed.connect(
            barrier_tags_changed,
            sender=BarrierInstance.tags.through
        )
