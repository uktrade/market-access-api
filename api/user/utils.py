from logging import getLogger
import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Profile

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
