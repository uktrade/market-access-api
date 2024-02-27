import logging

from django.apps import AppConfig
from django.conf import settings

from api.related_barriers import manager

logger = logging.getLogger(__name__)


class RelatedBarriersConfig(AppConfig):
    name = "api.related_barriers"

    def ready(self):
        logger.info(
            f"Init Related Barrier Manager: {settings.RELATED_BARRIER_DB_ON and manager.manager is None}"
        )

        if settings.RELATED_BARRIER_DB_ON and manager.manager is None:
            # Note: This can get called multiple times during lifetime of Django application. (startup and when
            # management commands run). We need to prevent that if the model is already initiated.
            manager.init()
