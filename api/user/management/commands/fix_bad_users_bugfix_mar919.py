from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from api.barriers.models import Barrier, BarrierUserHit
from api.collaboration.models import TeamMember
from api.interactions.models import ExcludeFromNotification, Mention, TeamMember
from api.user.models import (
    MyBarriersSavedSearch,
    Profile,
    SavedSearch,
    TeamBarriersSavedSearch,
)
from api.user_event_log.models import UserEvent

User = settings.AUTH_USER_MODEL

# These 5 functions have to be run in the same atomic DB operation


def update_user_attribute(bad_user: User, good_user: User) -> None:
    # Update the user attribute
    TeamMember.objects.filter(user=bad_user).update(user=good_user)
    BarrierUserHit.objects.filter(user=bad_user).update(user=good_user)
    MyBarriersSavedSearch.objects.filter(user=bad_user).update(user=good_user)
    Profile.objects.filter(user=bad_user).update(user=good_user)
    SavedSearch.objects.filter(user=bad_user).update(user=good_user)
    TeamBarriersSavedSearch.objects.filter(user=bad_user).update(user=good_user)
    TeamMember.objects.filter(user=bad_user).update(user=good_user)
    UserEvent.objects.filter(user=bad_user).update(user=good_user)

    # Update misc User attributes
    ExcludeFromNotification.objects.filter(excluded_user=bad_user).update(
        uexcluded_user=good_user
    )
    Mention.objects.filter(recipient=bad_user).update(recipient=good_user)


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
            user_obj = get_user_model()
            bad_user: User = user_obj.objects.get(id=options["bad_user_id"])
            good_user: User = user_obj.objects.get(id=options["good_user_id"])

            update_user_attribute(bad_user, good_user)
