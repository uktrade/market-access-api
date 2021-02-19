import csv
import itertools
import logging
from datetime import date

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from api.barriers.models import PublicBarrier
from api.barriers.public_data import public_release_to_s3
from api.metadata.constants import (TRADING_BLOCS, BarrierStatus,
                                    PublicBarrierStatus)
from api.metadata.utils import get_countries, get_sectors

logger = logging.getLogger(__name__)


class Metadata:
    def __init__(self):
        self.statuses = {name: id for id, name in BarrierStatus.choices}
        self.countries = {
            country["name"]: country["id"]
            for country in get_countries()
            if country["disabled_on"] is None
        }
        self.trading_blocs = {
            trading_bloc["name"]: trading_bloc["code"]
            for trading_bloc in TRADING_BLOCS.values()
        }
        self.sectors = {}
        for sector in get_sectors():
            if sector["disabled_on"] is None:
                if sector["level"] == 0:
                    self.sectors[sector["name"].lower()] = sector["id"]
                elif sector["level"] == 1:
                    self.sectors[sector["name"].lower()] = sector["parent"]["id"]

    def get_country(self, location_text):
        if location_text:
            clean_location_text = location_text.split("(")[0].strip()
            return self.countries.get(clean_location_text)

    def get_caused_by_trading_bloc(self, location_text):
        return "(European Union)" in location_text

    def get_trading_bloc(self, location_text):
        return self.trading_blocs.get(location_text)

    def get_status(self, status_text):
        clean_status_text = status_text.split("(")[0].strip()
        status = self.statuses.get(clean_status_text)
        if status is None:
            logger.info(f"Status not found: {status_text}")
        return status

    def get_sectors(self, sectors_text):
        sectors_text = sectors_text.strip()
        if not sectors_text or sectors_text in ("All", "N/A", "Multisector"):
            return []
        for sector_name in sectors_text.split(";"):
            sector = self.sectors.get(sector_name.lower().strip())
            if sector is None:
                logger.info(f"Sector not found: {sector_name}")
            yield sector

    def get_all_sectors(self, sectors_text):
        return sectors_text in ("All", "Multisector")


def create_public_barriers_from_csv(csv_file):
    metadata = Metadata()
    published_date = timezone.now()
    id_generator = itertools.count(1).__next__

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            public_barrier_id = id_generator()
            public_barrier = PublicBarrier(
                id=public_barrier_id,
                _title=row["Public title"],
                _summary=row["Public summary"],
                status=metadata.get_status(row["Status"]),
                status_date=date.fromisoformat(row["Status date"]),
                country=metadata.get_country(row["Location"]),
                caused_by_trading_bloc=metadata.get_caused_by_trading_bloc(row["Location"]),
                trading_bloc=metadata.get_trading_bloc(row["Location"]),
                sectors=metadata.get_sectors(row["Sectors"]),
                all_sectors=metadata.get_all_sectors(row["Sectors"]),
                _public_view_status=PublicBarrierStatus.PUBLISHED,
                first_published_on=published_date,
                last_published_on=published_date,
            )
            if row["Location"] and not public_barrier.country and not public_barrier.trading_bloc:
                logger.info(f"Location not found: {row['Location']}")

            yield public_barrier


class Command(BaseCommand):
    help = "Publish barriers from csv file"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="CSV file for importing public barriers")

    def handle(self, *args, **options):
        logger.setLevel(logging.DEBUG)

        if settings.DJANGO_ENV in ["local", "dev"]:
            csv_file = options["file"]
            logger.info("Reading barriers from csv file...")
            public_barriers = create_public_barriers_from_csv(csv_file)
            logger.info("Publishing barriers...")
            public_release_to_s3(public_barriers, force_publish=True)
        else:
            logger.info(f"Publishing from csv is disabled on {settings.DJANGO_ENV}")
