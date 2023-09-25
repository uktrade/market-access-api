from random import choice

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction
from faker.typing import Country

from api.barriers.models import Barrier
from api.core.exceptions import IllegalManagementCommandException
from api.metadata.models import Category, Organisation, BarrierTag, ExportType
from api.metadata.utils import get_countries
from tests.barriers.factories import BarrierFactory
from .data_anonymise import Command as AnonymiseCommand, SAFE_ENVIRONMENTS


class Command(BaseCommand):
    help = "Publish fake barriers"

    def add_arguments(self, parser):
        parser.add_argument("--quantity", type=int, help="Number of barriers to create")

    def handle(self, *args, **options):
        if settings.DJANGO_ENV in SAFE_ENVIRONMENTS:
            quantity = options["quantity"]
            self.stdout.write(f"Creating {quantity} mock barriers...")
            barrier_ids = []

            countries = get_countries()

            with transaction.atomic():
                category = Category.objects.first()
                government_organisation = Organisation.objects.first()
                tag = BarrierTag.objects.first()
                export_type = ExportType.objects.first()

                for x in range(quantity):
                    barrier = BarrierFactory(
                        status=2,
                        country=choice(countries)["id"],
                        export_description="Export description",
                        wto_profile__wto_should_be_notified=choice((True, False))
                    )

                    # adding some m2m fields which will get later anonymised and changed
                    barrier.categories.add(category)
                    barrier.organisations.add(government_organisation)
                    barrier.tags.add(tag)
                    barrier.export_types.add(export_type)
                    barrier_ids.append(barrier.id)

                barrier_queryset = Barrier.objects.filter(id__in=barrier_ids)
                AnonymiseCommand().anonymise(barrier_queryset)
        else:
            raise IllegalManagementCommandException(f"Creating fake barriers is disabled on {settings.DJANGO_ENV}")
