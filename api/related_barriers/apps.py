from django.apps import AppConfig
from api.related_barriers import model


class RelatedBarriersConfig(AppConfig):
    name = "api.related_barriers"

    def ready(self):
        db = model.create_db()
        model.set_db(database=db)

