from django.core.management.base import BaseCommand

from api.user.models import SavedSearch


class Command(BaseCommand):
    """
    Marks all saved searches as notified

    To be removed after deploy of saved search notifications.
    """

    help = "Marks all saved searches as notified"

    def handle(self, *args, **options):
        count = 0
        for saved_search in SavedSearch.objects.filter(filters__isnull=False):
            saved_search.mark_as_notified()
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Success: {count} saved searches marked as notified")
        )
