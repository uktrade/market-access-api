from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from api.user.fix_bad_user_helper import move_all_data_from_bad_user_to_good_user
from api.user.helpers import update_user_profile_user_id
from api.user.models import Profile
from api.user.staff_sso import sso

UserModel = get_user_model()


class Command(BaseCommand):
    """
    https://uktrade.atlassian.net/browse/MAR-952

    This is the fix to move all the auth_user objects over to the SSO system
    """

    help = "this command will move all user over to the SSO system"

    def handle(self, *args, **options):
        profiles_with_guid = Profile.objects.filter(
            ~Q(sso_user_id__isnull=True)
        )  # If sso_user_id is not null
        for profile in profiles_with_guid:
            update_user_profile_user_id(profile.user, profile.sso_user_id)

        # At this point every valid user has the username set to sso email_user_id
        # and the user has one profile with a valid ss_user_id
        profiles_with_guid = Profile.objects.filter(
            Q(sso_user_id__isnull=True)
        )  # If sso_user_id is null
        for profile in profiles_with_guid:
            sso_user = sso.get_user_details_by_email(profile.user.username)
            user = UserModel.objects.filter(username=sso_user["email_user_id"])
            # No existing user from the SSO exists so change this user into an SSO user
            if not user.exists():
                update_user_profile_user_id(profile.user, sso_user["email_user_id"])
                continue

            # If we have duplicate User objects, The email in this username points to
            # an existing profile. Move everything over to the existing profile and
            # delete this duplicate
            good_user = user.first()
            bad_user = profile.user
            with transaction.atomic():
                move_all_data_from_bad_user_to_good_user(bad_user, good_user)
                bad_user.delete()
                continue
