import datetime

from django.conf import settings
from django.core.management import BaseCommand, call_command
from simple_history import models, utils
from simple_history.exceptions import NotHistoricalModelError

from api.barriers.models import Barrier, PublicBarrier
from api.core.exceptions import IllegalManagementCommandException
from api.history.models import CachedHistoryItem

from .data_anonymise import SAFE_ENVIRONMENTS


class Command(BaseCommand):
    help = "Delete all historical records"

    def handle(self, *args, **options):
        if settings.DJANGO_ENV in SAFE_ENVIRONMENTS:
            reported_on = datetime.datetime(
                month=2, day=1, year=2021, tzinfo=datetime.timezone.utc
            )
            history_date = datetime.datetime(
                month=1, day=1, year=2021, tzinfo=datetime.timezone.utc
            )

            self.stdout.write("Updating barrier reported_on")
            Barrier.objects.all().update(reported_on=reported_on)

            self.stdout.write("Deleting all historical records")
            for model in models.registered_models.values():
                try:
                    history_model = utils.get_history_model_for_model(model)
                    history_model.objects.all().delete()
                    self.stdout.write(
                        f"Deleted {history_model.__name__} historical records"
                    )
                except NotHistoricalModelError:
                    continue

            # now we've deleted history, we can restore it again
            self.stdout.write("Restoring history")
            call_command("populate_history", "--auto")

            self.stdout.write("Setting history date back")
            for model in models.registered_models.values():
                try:
                    history_model = utils.get_history_model_for_model(model)
                    history_model.objects.all().update(history_date=history_date)
                except NotHistoricalModelError:
                    continue

            self.stdout.write("Deleting Cached History items")
            CachedHistoryItem.objects.all().delete()

            self.stdout.write("Setting published barrier date")
            PublicBarrier.objects.all().update(published_on=reported_on)
        else:
            raise IllegalManagementCommandException(
                f"Deleting historical records is disabled on {settings.DJANGO_ENV}"
            )
