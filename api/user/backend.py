import logging

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import get_client, get_profile, has_valid_token

from api.user.models import Profile

User = get_user_model()


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        print(f"STUB:1: {request.COOKIES}")
        logging.warning(f"STUB:1: {request.COOKIES}")
        client = get_client(request)
        print(f"STUB:2: {client}")
        logging.warning(f"STUB:2: {client}")
        if has_valid_token(client):
            profile = get_profile(client)
            print(f"STUB:3: {profile}")
            logging.warning(f"STUB:3: {profile}")
            return self.verify_user_object(profile)
        print(f"STUB:4: NO USER")
        logging.warning(f"STUB:4: NO USER")
        return None

    @staticmethod
    def _build_profile(profile: Profile, email: str, raw_profile: dict) -> Profile:
        profile.sso_user_id = raw_profile["user_id"]
        profile.sso_email_user_id = raw_profile["email_user_id"]
        profile.user.email = raw_profile.get("contact_email") or email
        # contact emails ?
        profile.user.first_name = raw_profile["first_name"]  # might change over time
        profile.user.last_name = raw_profile["last_name"]  # might change over time
        profile.user.username = raw_profile["email_user_id"]  #
        profile.save()  # This saves the user object as well.

        return profile

    @staticmethod
    def verify_user_object(raw_profile) -> User:
        print(f"STUB:5: {raw_profile}")
        logging.warning(f"STUB:5: {raw_profile}")
        email: str = raw_profile["email"]

        # If possible use the existing profile object
        profiles: QuerySet = Profile.objects.filter(
            Q(sso_email_user_id=raw_profile["email_user_id"])
            | Q(sso_user_id=raw_profile["user_id"])
        )
        num_of_profile: int = profiles.count()
        if num_of_profile > 1:
            raise NotImplementedError(
                "The system has found multiple User profiles for you. The fix for this is being written"
            )  # TODO: handle duplicate profiles bug
        if num_of_profile == 1:
            p = CustomAuthbrokerBackend._build_profile(
                profiles.first(), email, raw_profile
            )
            return p.user

        # Try to get an existing old bad user object or create a new object
        try:
            user: User = User.objects.get(username=email)
        except User.DoesNotExist:
            user: User = User()
            user.save()  # initialise the profile objects

        p = CustomAuthbrokerBackend._build_profile(user.profile, email, raw_profile)
        return p.user
