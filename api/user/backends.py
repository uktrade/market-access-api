from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import (
    get_client,
    get_profile,
    has_valid_token,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        client = get_client(request)
        if has_valid_token(client):
            profile = get_profile(client)
            return self.verify_user_object(profile)
        return None

    @staticmethod
    def verify_user_object(profile):
        # Look for legacy style user record
        profile = Profile.objects.filter(sso_user_id=profile["user_id"]).first()

        if profile:
            profile.sso_email_user_id = profile["email_user_id"]
            profile.user.email = profile["email"]
            # contact emails ?
            user.first_name = profile["first_name"]  # might change over time
            user.last_name = profile["last_name"]  # might change over time
            user.save()

            return user
        else:
            profile = Profile.objects.filter(sso_email_user_id=profile["email_user_id"]).first()

            if profile:
                profile.sso_email_user_id = profile["email_user_id"]
                profile.user.email = profile["email"]
                # contact emails ?
                user.first_name = profile["first_name"]  # might change over time
                user.last_name = profile["last_name"]  # might change over time
                user.save()

                return user
            else:
                # New users or problem users
                user = User(
                    username=profile["email"],
                    email=profile["email"],
                    first_name=profile["first_name"],
                    last_name=profile["last_name"],
                    profile = Profile(
                        sso_email_user_id=profile["email_user_id"],
                        #location="foo",
                        #internal="bar",
                    )
                )
                user.set_unusable_password()
                user.save()

                return user