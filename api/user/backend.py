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
            profile_obj.save()

            return profile_obj

        # Look for current style user record
        profile = Profile.objects.filter(
            Q(sso_email_user_id=raw_profile["email_user_id"])
        ).first()
        if profile:
            p = _build_profile(profile)
            return p.user

        # Look for legacy style user record
        profile = Profile.objects.filter(Q(sso_user_id=raw_profile["user_id"])).first()
        if profile:
            p = _build_profile(profile)
            return p.user

        # else:
        #     profile = Profile.objects.filter().first()

        #     if profile:
        #         profile.sso_email_user_id = profile["email_user_id"]
        #         profile.user.email = profile["email"]
        #         # contact emails ?
        #         user.first_name = profile["first_name"]  # might change over time
        #         user.last_name = profile["last_name"]  # might change over time
        #         user.save()

        #         return user
        #     else:
        #         # New users or problem users
        #         user = User(
        #             username=profile["email"],
        #             email=profile["email"],
        #             first_name=profile["first_name"],
        #             last_name=profile["last_name"],
        #             profile=Profile(
        #                 sso_email_user_id=raw_profile["email_user_id"],
        #                 # location="foo",
        #                 # internal="bar",
        #             ),
        #         )
        #         user.set_unusable_password()
        #         user.save()

        #         return user
