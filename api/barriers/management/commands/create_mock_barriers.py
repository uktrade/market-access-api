import datetime
import itertools
import random
from datetime import timezone

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from api.barriers.models import PublicBarrier, Barrier
from api.barriers.public_data import public_release_to_s3
from api.metadata.constants import BarrierStatus, PublicBarrierStatus
from api.metadata.utils import (
    get_countries,
    get_sectors,
    get_trading_bloc_by_country_id,
)
from tests.barriers.factories import BarrierFactory
from .data_anonymise import Command as AnonymiseCommand

class Command(BaseCommand):
    help = "Publish fake barriers"

    def add_arguments(self, parser):
        parser.add_argument("--quantity", type=int, help="Number of barriers to create")

    def handle(self, *args, **options):
        if settings.DJANGO_ENV in ["local", "dev"]:
            quantity = options["quantity"]
            self.stdout.write(f"Creating {quantity} fake barriers...")
            barrier_ids = []

            with transaction.atomic():
                for x in range(quantity):
                    barrier = BarrierFactory()
                    barrier_ids.append(barrier.id)

                barrier_queryset = Barrier.objects.filter(id__in=barrier_ids)
                AnonymiseCommand().anonymise(barrier_queryset)
                print("asd")
        else:
            self.stdout.write(
                f"Creating fake barriers is disabled on {settings.DJANGO_ENV}"
            )
