from django.contrib.auth import get_user_model

from api.core.utils import cleansed_username
from .models import Profile
from .staff_sso import sso

UserModel = get_user_model()


def get_django_user_by_sso_user_id(sso_user_id):
    try:
        user_profile = Profile.objects.get(sso_user_id=sso_user_id)
        user = user_profile.user
    except Profile.DoesNotExist:
        sso_user = sso.get_user_details_by_id(sso_user_id)
        email = sso_user.get("email")
        first_name = sso_user.get("first_name")
        last_name = sso_user.get("last_name")

        try:
            user = UserModel.objects.get(
                username=sso_user["email_user_id"],
            )
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except UserModel.DoesNotExist:
            user = UserModel(
                username=sso_user["email_user_id"],
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.save()

        user.profile.sso_email_user_id = sso_user["email_user_id"]
        user.profile.sso_user_id = sso_user_id
        user.profile.save()

    return user


def update_user_profile(user, auth_token):
    context = {"token": auth_token}
    sso_user = sso.get_logged_in_user_details(context)
    user.username = sso_user.get("email_user_id")
    user.email = sso_user.get("email")
    user.first_name = sso_user["first_name"]
    user.last_name = sso_user["last_name"]
    user.save()
    # Profile
    user.profile.sso_user_id = sso_user["user_id"]
    user.profile.sso_email_user_id = sso_user["email_user_id"]
    user.profile.save()


def update_user_profile_user_id(user, user_id):
    sso_user = sso.get_user_details_by_id(user_id)
    user.username = sso_user.get("email_user_id")
    user.email = sso_user.get("email")
    user.first_name = sso_user["first_name"]
    user.last_name = sso_user["last_name"]

    # Profile
    user.profile.sso_user_id = sso_user["user_id"]
    user.profile.sso_email_user_id = sso_user["email_user_id"]

    user.save()


def has_profile(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return False


def get_username(user, context=None):
    username = cleansed_username(user)
    if "." in username:
        sso_me = sso.get_logged_in_user_details(context)
        if sso_me:
            return f"{sso_me.get('first_name', '')} {sso_me.get('last_name', '')}"
    return username
