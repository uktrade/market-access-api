from django.contrib.auth.models import User
from django.core.management import BaseCommand

from api.user.staff_sso import sso


class Command(BaseCommand):
    help = "Take a group of users and call SSO to copy over a more recent email value"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email_domain",
            type=str,
            help="The domain extension (everything after the @) of an email you want to update",
        )
        parser.add_argument(
            "--dry_run",
            type=bool,
            help="Bool to decide whether to call SSO",
            default=False,
        )

    def handle(self, *args, **options):

        # Source the passed argumentsß
        email_domain_arg = options["email_domain"]
        dry_run = options["dry_run"]

        # Get the initial list of users
        users_list = User.objects.all()

        # Take full list of users and build a new list of users who
        # have the same email domain as the one passed to the command
        if email_domain_arg:
            domain_specific_users_list = []
            for user in users_list:
                users_email_domain = user.email.split("@")[1]
                if users_email_domain == email_domain_arg:
                    domain_specific_users_list.append(user)
            users_list = domain_specific_users_list

        # For every user in the users list, call SSO to obtain their latest
        # information. If the emails do not match, update what we have in the DB
        # with the email stored in SSO.
        for user in users_list:
            sso_user = None
            if dry_run is not True:
                sso_user = sso.get_user_details_by_email_user_id(
                    user.sso_email_user_id,
                )
            if sso_user and user.email != sso_user["email"]:
                user.email = sso_user["email"]
                user.save()
