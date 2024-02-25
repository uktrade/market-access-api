from django.apps import AppConfig
from django.conf import settings

from api.related_barriers import model


class RelatedBarriersConfig(AppConfig):
    name = "api.related_barriers"

    def ready(self):
        if settings.RELATED_BARRIER_DB_ON:
            db = model.create_db()
            model.set_db(database=db)
