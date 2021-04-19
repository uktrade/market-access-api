from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """
    https://uktrade.atlassian.net/browse/MAR-919

    This is the fix to the missing mentions problem explained in ticket MAR-919
    """

    help = "this command will move all data from the bad user to the good user"

    def add_parametter(self, parser):
        parser.add_argument(
            "bad_user_id", type=int, help="The rowId of the bad User record"
        )
        parser.add_argument(
            "good_user_id", typw=str, help="The rowId of the good User record"
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            pass
