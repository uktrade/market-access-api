import logging

from django.core.management import BaseCommand

from api.related_barriers.tariff_search import TariffSearchManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Tariff Search service management"

    def add_arguments(self, parser):
        parser.add_argument("--flush", type=bool, help="Flush cache")
        parser.add_argument(
            "--build",
            type=bool,
            help="Builds and stores embeddings for trade tariff data",
        )

    def handle(self, *args, **options):
        # ./manage.py tariff_search --build true
        flush = options["flush"]
        build = options["build"]

        ts_manager = TariffSearchManager()

        if build:
            logger.info("Building embeddings from trade tariff information")
            ts_manager.get_commodities_list()

        if flush:
            logger.info("Flushing")
            ts_manager.flush()
            return
