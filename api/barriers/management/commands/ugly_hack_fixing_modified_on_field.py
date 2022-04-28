from django.core.management import BaseCommand
from django.db.models import Max, OuterRef, Subquery

from ...models import Barrier


class Command(BaseCommand):
    """sets the modified_on field of all barriers to the date of the last history item"""

    help = "sets the modified_on field of all barriers to the date of their most recent history item"

    def handle(self, *args, **options):
        Barrier.objects.update(
            modified_on=Subquery(
                Barrier.objects.filter(pk=OuterRef("pk")).values_list(
                    Max("cached_history_items__date")
                )[:1]
            )
        )
