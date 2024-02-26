from django.apps import AppConfig
from django.conf import settings

from api.related_barriers import model


class RelatedBarriersConfig(AppConfig):
    name = "api.related_barriers"

    def ready(self):
        if settings.RELATED_BARRIER_DB_ON and model.db is None:
            # Note: This can get called multiple times during lifetime of Django application. (startup and when
            # management commands run). We need to prevent that if the model is already initiated.
            db = model.create_db()
            model.set_db(database=db)
