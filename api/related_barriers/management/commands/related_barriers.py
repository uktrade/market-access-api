import logging
import time

from django.core.management import BaseCommand

from api.related_barriers import manager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Related Barrier service management"

    def add_arguments(self, parser):
        parser.add_argument("--flush", type=bool, help="Flush cache")
        parser.add_argument("--reindex", type=bool, help="Reindex cache")
        parser.add_argument(
            "--stats", type=bool, help="Get Related Barrier cache stats"
        )

    def handle(self, *args, **options):
        flush = options["flush"]
        reindex = options["reindex"]
        stats = options["stats"]

        rb_manager = manager.RelatedBarrierManager()

        barrier_count = len(rb_manager.get_barrier_ids())

        if stats:
            logger.info(f"Barrier Count: {barrier_count}")

        if reindex:
            logger.info(f"Reindexing {barrier_count} barriers")
            data = manager.get_data()

            rb_manager.flush()

            s = time.time()
            rb_manager.set_data(data)
            end = time.time()
            logger.info("Training time: ", end - s)
            return

        if flush:
            logger.info("Flushing")
            rb_manager.flush()
            return
