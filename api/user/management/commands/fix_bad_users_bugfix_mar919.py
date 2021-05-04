from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.models import (
    Barrier,
    BarrierReportStage,
    BarrierUserHit,
    PublicBarrier,
)
from api.documents.models import Document
from api.interactions.models import (
    ExcludeFromNotification,
    Interaction,
    Mention,
    PublicBarrierNote,
    TeamMember,
)
from api.metadata.models import BarrierTag
from api.user.models import MyBarriersSavedSearch, SavedSearch, TeamBarriersSavedSearch
from api.user_event_log.models import UserEvent


# These 5 functions have to be run in the same atomic DB operation
def update_user_attribute(
    bad_user: settings.AUTH_USER_MODEL, good_user: settings.AUTH_USER_MODEL
) -> None:
    # Update the user attribute
    TeamMember.objects.filter(user=bad_user).update(user=good_user)
    SavedSearch.objects.filter(user=bad_user).update(user=good_user)

    UserEvent.objects.filter(user=bad_user).update(user=good_user)
    Mention.objects.filter(recipient=bad_user).update(recipient=good_user)

    # Explicitly delete one-to-one user relations for bad users.
    if not BarrierUserHit.objects.filter(user=good_user).exists():
        BarrierUserHit.objects.filter(user=bad_user).update(user=good_user)
    if not MyBarriersSavedSearch.objects.filter(user=good_user).exists():
        MyBarriersSavedSearch.objects.filter(user=bad_user).update(user=good_user)
    if MyBarriersSavedSearch.objects.filter(user=bad_user).exists():
        MyBarriersSavedSearch.objects.filter(user=bad_user).delete()
    if not TeamBarriersSavedSearch.objects.filter(user=good_user).exists():
        TeamBarriersSavedSearch.objects.filter(user=bad_user).update(user=good_user)
    if TeamBarriersSavedSearch.objects.filter(user=bad_user).exists():
        TeamBarriersSavedSearch.objects.filter(user=bad_user).delete()

    # These are the misc User attributes. They are all one-to-one relations
    if not ExcludeFromNotification.objects.filter(excluded_user=good_user).exists():
        ExcludeFromNotification.objects.filter(excluded_user=bad_user).update(
            excluded_user=good_user
        )
    if ExcludeFromNotification.objects.filter(
        Q(excluded_user=bad_user) & ~Q(excluded_user=good_user)
    ).exists():
        ExcludeFromNotification.objects.filter(excluded_user=bad_user).delete()


def update_basemodel_attributes(
    bad_user: settings.AUTH_USER_MODEL, good_user: settings.AUTH_USER_MODEL
) -> None:
    # update the created_by attribute
    Barrier.objects.filter(created_by=bad_user).update(created_by=good_user)
    BarrierReportStage.objects.filter(created_by=bad_user).update(created_by=good_user)
    BarrierTag.objects.filter(created_by=bad_user).update(created_by=good_user)
    Document.objects.filter(created_by=bad_user).update(created_by=good_user)
    EconomicAssessment.objects.filter(created_by=bad_user).update(created_by=good_user)
    EconomicImpactAssessment.objects.filter(created_by=bad_user).update(
        created_by=good_user
    )
    ExcludeFromNotification.objects.filter(created_by=bad_user).update(
        created_by=good_user
    )
    Interaction.objects.filter(created_by=bad_user).update(created_by=good_user)
    Mention.objects.filter(created_by=bad_user).update(created_by=good_user)
    PublicBarrier.objects.filter(created_by=bad_user).update(created_by=good_user)
    PublicBarrierNote.objects.filter(created_by=bad_user).update(created_by=good_user)
    ResolvabilityAssessment.objects.filter(created_by=bad_user).update(
        created_by=good_user
    )
    StrategicAssessment.objects.filter(created_by=bad_user).update(created_by=good_user)
    TeamMember.objects.filter(created_by=bad_user).update(created_by=good_user)

    # update the modified_by attribute
    Barrier.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    BarrierReportStage.objects.filter(modified_by=bad_user).update(
        modified_by=good_user
    )
    BarrierTag.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    Document.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    EconomicAssessment.objects.filter(modified_by=bad_user).update(
        modified_by=good_user
    )
    EconomicImpactAssessment.objects.filter(modified_by=bad_user).update(
        modified_by=good_user
    )
    ExcludeFromNotification.objects.filter(modified_by=bad_user).update(
        modified_by=good_user
    )
    Interaction.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    Mention.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    PublicBarrier.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    PublicBarrierNote.objects.filter(modified_by=bad_user).update(modified_by=good_user)
    ResolvabilityAssessment.objects.filter(modified_by=bad_user).update(
        modified_by=good_user
    )
    StrategicAssessment.objects.filter(modified_by=bad_user).update(
        modified_by=good_user
    )
    TeamMember.objects.filter(modified_by=bad_user).update(modified_by=good_user)


def update_achivable_attributes(
    bad_user: settings.AUTH_USER_MODEL, good_user: settings.AUTH_USER_MODEL
) -> None:
    # update the archived_by attribute
    Barrier.objects.filter(archived_by=bad_user).update(archived_by=good_user)
    Document.objects.filter(archived_by=bad_user).update(archived_by=good_user)
    EconomicAssessment.objects.filter(archived_by=bad_user).update(
        archived_by=good_user
    )
    EconomicImpactAssessment.objects.filter(archived_by=bad_user).update(
        archived_by=good_user
    )
    Interaction.objects.filter(archived_by=bad_user).update(archived_by=good_user)
    PublicBarrier.objects.filter(archived_by=bad_user).update(archived_by=good_user)
    PublicBarrierNote.objects.filter(archived_by=bad_user).update(archived_by=good_user)
    StrategicAssessment.objects.filter(archived_by=bad_user).update(
        archived_by=good_user
    )
    TeamMember.objects.filter(archived_by=bad_user).update(archived_by=good_user)


def update_fullyachivable_attributes(
    bad_user: settings.AUTH_USER_MODEL, good_user: settings.AUTH_USER_MODEL
) -> None:
    # update the unarchived_by attribute
    Barrier.objects.filter(unarchived_by=bad_user).update(unarchived_by=good_user)
    PublicBarrier.objects.filter(unarchived_by=bad_user).update(unarchived_by=good_user)


def update_approval_attributes(
    bad_user: settings.AUTH_USER_MODEL, good_user: settings.AUTH_USER_MODEL
) -> None:
    # update the reviewed_by attribute
    EconomicAssessment.objects.filter(reviewed_by=bad_user).update(
        reviewed_by=good_user
    )
    StrategicAssessment.objects.filter(reviewed_by=bad_user).update(
        reviewed_by=good_user
    )
    ResolvabilityAssessment.objects.filter(reviewed_by=bad_user).update(
        reviewed_by=good_user
    )


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

            update_user_attribute(bad_user, good_user)
            update_basemodel_attributes(bad_user, good_user)
            update_achivable_attributes(bad_user, good_user)
            update_fullyachivable_attributes(bad_user, good_user)
            update_approval_attributes(bad_user, good_user)

            bad_user.delete()
