from random import choice

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from api.barriers.models import Barrier
from api.core.exceptions import IllegalManagementCommandException
from api.metadata.models import BarrierTag, ExportType, Organisation
from api.metadata.utils import get_countries
from tests.barriers.factories import BarrierFactory, fuzzy_date

from .data_anonymise import SAFE_ENVIRONMENTS
from .data_anonymise import Command as AnonymiseCommand


class Command(BaseCommand):
    help = "Build a set of fake barriers"

    def add_arguments(self, parser):
        parser.add_argument("--quantity", type=int, help="Number of barriers to create")

    def handle(self, *args, **options):
        if settings.DJANGO_ENV in SAFE_ENVIRONMENTS:
            quantity = options["quantity"]
            self.stdout.write(f"Creating {quantity} mock barriers...")
            barrier_ids = []

            countries = get_countries()

            with transaction.atomic():
                government_organisation = Organisation.objects.first()
                tag = BarrierTag.objects.first()
                export_type = ExportType.objects.first()

                for x in range(quantity):
                    status = choice((2, 3, 4, 5, 6))
                    status_date = fuzzy_date()

                    barrier = BarrierFactory(
                        status=status,
                        country=choice(countries)["id"],
                        export_description="Export description",
                        wto_profile__wto_should_be_notified=choice((True, False)),
                        sectors=["aa22c9d2-5f95-e211-a939-e4115bead28a"],
                        status_date=status_date,
                    )

                    # adding some m2m fields which will get later anonymised and changed
                    barrier.organisations.add(government_organisation)
                    barrier.tags.add(tag)
                    barrier.export_types.add(export_type)
                    barrier_ids.append(barrier.id)

                barrier_queryset = Barrier.objects.filter(id__in=barrier_ids)
                AnonymiseCommand().anonymise(barrier_queryset)
        else:
            raise IllegalManagementCommandException(
                f"Creating fake barriers is disabled on {settings.DJANGO_ENV}"
            )
