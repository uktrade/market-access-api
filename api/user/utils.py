from .models import Profile
from .staff_sso import StaffSSO
from api.core.utils import cleansed_username

sso = StaffSSO()

def has_profile(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return False

def get_sso_field(field_name, default=None, context=None):
    sso_me = sso.get_logged_in_user_details(context)
    if sso_me:
        return sso_me.get(field_name, default)
    return default

def get_username(user, context=None):
    username = cleansed_username(user)
    if "." in username:
        sso_me = sso.get_logged_in_user_details(context)
        if sso_me:
            return f"{sso_me.get('first_name', '')} {sso_me.get('last_name', '')}"
    return username
