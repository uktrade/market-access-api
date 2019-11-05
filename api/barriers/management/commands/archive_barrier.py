from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from api.barriers.models import BarrierInstance


class Command(BaseCommand):
    help = 'Archives a specific barrier'

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help="Requesting user's email address",
            dest="username",
        )
        parser.add_argument(
            "--barrier_id",
            help="GUID of barrier to archive",
            dest="barrier_id",
        )

    def handle(self, *args, **options):
        username = options["username"]
        barrier_id = options["barrier_id"]

        if username is None:
            raise CommandError(
                'Please supply the email of the requesting user, using --username'
            )

        if barrier_id is None:
            raise CommandError(
                'Please supply a barrier id in GUID format using --barrier_id'
            )

        user_model = get_user_model()

        user = user_model.objects.filter(
            username=username
        ).first()

        if user is None:
            raise CommandError(
                'Cannot find specified user "{}"'.format(
                    username
                )
            )

        try:
            barrier = BarrierInstance.objects.get(
                id=barrier_id
            )
        except BarrierInstance.DoesNotExist:
            raise CommandError(
                'Cannot find specified barrier "{}"'.format(
                    barrier_id
                )
            )

        barrier.archive(user=user)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully archived barrier "{}"'.format(
                    barrier_id
                )
            )
        )
