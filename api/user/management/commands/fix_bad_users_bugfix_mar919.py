from api.user.fix_bad_user_helper import move_all_data_from_bad_user_to_good_user

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings


class Command(BaseCommand):
    """
    https://uktrade.atlassian.net/browse/MAR-919

    This is the fix to the missing mentions problem explained in ticket MAR-919
    """

    help = "this command will move all data from the bad user to the good user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--bad_user_id", type=int, help="The rowId of the bad User record"
        )
        parser.add_argument(
            "--good_user_id", type=int, help="The rowId of the good User record"
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            user_obj = get_user_model()
            bad_user: settings.AUTH_USER_MODEL = user_obj.objects.get(
                id=options["bad_user_id"]
            )
            good_user: settings.AUTH_USER_MODEL = user_obj.objects.get(
                id=options["good_user_id"]
            )

            move_all_data_from_bad_user_to_good_user(bad_user, good_user)

            good_user.username = bad_user.username
            bad_user.delete()
            good_user.save()
