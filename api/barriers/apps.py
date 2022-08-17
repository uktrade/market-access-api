from django.apps import AppConfig


class BarriersConfig(AppConfig):
    name = "api.barriers"

    def ready(self):
        from django.db.models.signals import m2m_changed, post_save, pre_save

        from .models import Barrier, PublicBarrier, PublicBarrierLightTouchReviews
        from .signals.handlers import (
            barrier_categories_changed,
            barrier_completion_percentage_changed,
            barrier_completion_top_priority_barrier_resolved,
            barrier_organisations_changed,
            barrier_priority_approval_email_notification,
            barrier_tags_changed,
            public_barrier_categories_changed,
            public_barrier_content_update,
            public_barrier_light_touch_reviews_changed,
        )

        m2m_changed.connect(
            barrier_organisations_changed, sender=Barrier.organisations.through
        )
        m2m_changed.connect(
            barrier_categories_changed, sender=Barrier.categories.through
        )
        m2m_changed.connect(barrier_tags_changed, sender=Barrier.tags.through)
        m2m_changed.connect(
            public_barrier_categories_changed, sender=PublicBarrier.categories.through
        )

        pre_save.connect(public_barrier_content_update, sender=PublicBarrier)

        post_save.connect(barrier_completion_percentage_changed, sender=Barrier)

        post_save.connect(
            barrier_completion_top_priority_barrier_resolved, sender=Barrier
        )

        post_save.connect(barrier_priority_approval_email_notification, sender=Barrier)

        post_save.connect(
            public_barrier_light_touch_reviews_changed,
            sender=PublicBarrierLightTouchReviews,
        )
