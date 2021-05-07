from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import (
    get_client,
    get_profile,
    has_valid_token,
)
from django.contrib.auth import get_user_model
from django.db.models import Q

from api.user.models import Profile

User = get_user_model()


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        client = get_client(request)
        if has_valid_token(client):
            profile = get_profile(client)
            return self.verify_user_object(profile)
        return None

    @staticmethod
    def verify_user_object(raw_profile) -> User:
        email = raw_profile["email"]

        def _build_profile(profile_obj):
            profile_obj.sso_user_id = raw_profile["user_id"]
            profile_obj.sso_email_user_id = raw_profile["email_user_id"]
            profile_obj.user.email = raw_profile.get("contact_email") or email
            # contact emails ?
            profile_obj.user.first_name = raw_profile[
                "first_name"
            ]  # might change over time
            profile_obj.user.last_name = raw_profile[
                "last_name"
            ]  # might change over time
            profile_obj.user.is_active = True
            profile_obj.user.is_staff = True
            profile_obj.user.username = raw_profile["email_user_id"]  #
            profile_obj.save()  # This saves the user object as well.

            return profile_obj

        # If possible use the existing profile object
        profile = Profile.objects.filter(
            Q(sso_email_user_id=raw_profile["email_user_id"])
            | Q(sso_user_id=raw_profile["user_id"])
        )
        num_of_profile = profile.count()
        if num_of_profile > 1:
            pass  # TODO: handle duplicate profiles bug
        if num_of_profile == 1:
            p = _build_profile(profile.first())
            return p.user

        # Try to get an existing old bad user object or create a new object
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            user = User()
            user.save()  # initialise the profile objects

        p = _build_profile(user.profile)
        return p.user
