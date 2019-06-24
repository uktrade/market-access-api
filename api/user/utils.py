from logging import getLogger
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .models import Profile
from api.core.utils import cleansed_username

UserModel = get_user_model()
logger = getLogger(__name__)


def has_profile(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return False

def get_sso_user_data(context):
    if not settings.SSO_ENABLED:
        return None
    url = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INFO_URL"]
    token = context.get("token", None)
    if token is None:
        logger.warning("auth bearer token is empty")
    auth_string = f"Bearer {token}"
    headers = {
        'Authorization': auth_string,
        'Cache-Control': "no-cache"
        }
    try:
        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning("User info endpoint on SSO was not successful")
            return None
    except Exception as exc:
        logger.error(f"Error occurred while requesting user info from SSO, {exc}")
        return None

def get_sso_field(field_name, default=None, context=None):
    # sso_me = cache.get_or_set("sso_me", get_sso_user_data(context), 72000)
    sso_me = get_sso_user_data(context)
    if sso_me:
        return sso_me.get(field_name, default)
    return default

def get_username(user, context=None):
    username = cleansed_username(user)
    # sso_me = cache.get_or_set("sso_me", get_sso_user_data(context), 72000)
    sso_me = get_sso_user_data(context)
    if sso_me:
        return f"{sso_me.get('first_name', '')} {sso_me.get('last_name', '')}"
    return username
