import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db.models import Max
from oauth2_provider.models import get_access_token_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill last login date on user based on 10 hour oauth expiry"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry_run",
            type=bool,
            default=False,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        AccessToken = get_access_token_model()
        User = get_user_model()

        values_qs = (
            AccessToken.objects.order_by("user__id")
            .filter(user__last_login__isnull=True)
            .values("user")
            .annotate(expires=Max("expires"))
        )

        # Default expiry is 10 hours so assume last login was (expires - 10 hours)
        user_to_expires = {
            d["user"]: d["expires"] - timedelta(hours=10)
            for d in values_qs
            if d["expires"]
        }

        users = User.objects.filter(id__in=user_to_expires.keys())

        users_to_update = []
        for user in users:
            user.last_login = user_to_expires[user.id]
            users_to_update.append(user)

        if not dry_run:
            updated_count = User.objects.bulk_update(users_to_update, ["last_login"])
            logger.info(f"Users updates: {updated_count}")
        else:
            logger.info(f"Potential user updates: {len(users_to_update)}")
