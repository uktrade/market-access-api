from django.core.management import BaseCommand

from api.barriers.history.manager import HistoryManager
from api.barriers.models import BarrierInstance
from api.history.models import CachedHistoryItem


class Command(BaseCommand):
    help = "Cache history items"

    def add_arguments(self, parser):
        parser.add_argument("--barrier", type=str, help="Barrier ID")

    def handle(self, *args, **options):
        if options.get("barrier"):
            barrier = BarrierInstance.objects.get(pk=options["barrier"])
            self.generate_history_for_barrier(barrier)

        else:
            barrier_count = 0
            for barrier in BarrierInstance.objects.all():
                self.generate_history_for_barrier(barrier)
                self.stdout.flush()
                self.stdout.write(f"{barrier_count} barriers cached", ending="\r")
                barrier_count += 1

    def generate_history_for_barrier(self, barrier):
        history_items = HistoryManager.get_full_history(barrier)
        for item in history_items:
            CachedHistoryItem.create_from_history_item(item)
