from django.core.management.base import BaseCommand

from api.user.models import SavedSearch


class Command(BaseCommand):
    help = "Marks all saved searches as seen"

    def handle(self, *args, **options):
        count = 0
        for saved_search in SavedSearch.objects.filter(filters__isnull=False):
            saved_search.mark_as_seen()
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Success: {count} saved searches updated")
        )
