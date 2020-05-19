from django.core.management.base import BaseCommand

from api.user.tasks import send_notification_emails


class Command(BaseCommand):
    help = "Sends notification emails about additions and updates to saved searches"

    def handle(self, *args, **options):
        send_notification_emails()

        self.stdout.write(
            self.style.SUCCESS(f"Saved search notification emails scheduled")
        )
