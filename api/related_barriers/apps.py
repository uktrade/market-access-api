import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class RelatedBarriersConfig(AppConfig):
    name = "api.related_barriers"
