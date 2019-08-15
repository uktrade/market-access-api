from logging import getLogger
import requests

from django.conf import settings

logger = getLogger(__name__)


class StaffSSO:
    def get_logged_in_user_details(self, context):
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

    def get_user_details_by_id(self, user_id):
        if not settings.SSO_ENABLED:
            return None
        url = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INTROSPECT_URL"]
        token = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_AUTH_TOKEN"]
        auth_string = f"Bearer {token}"
        params = {
            "user_id": user_id
        }
        headers = {
            'Authorization': auth_string,
            'Cache-Control': "no-cache"
            }
        try:
            response = requests.request(
                "GET",
                url,
                params=params,
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Introspect endpoint on SSO was not successful")
                return None
        except Exception as exc:
            logger.error(f"Error occurred while requesting user info from SSO, {exc}")
            return None

    def get_user_details_by_email(self, email):
        if not settings.SSO_ENABLED:
            return None
        url = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INTROSPECT_URL"]
        token = settings.OAUTH2_PROVIDER["RESOURCE_SERVER_AUTH_TOKEN"]
        auth_string = f"Bearer {token}"
        params = {
            "email": email
        }
        headers = {
            'Authorization': auth_string,
            'Cache-Control': "no-cache"
            }
        try:
            response = requests.request(
                "GET",
                url,
                params=params,
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Introspect endpoint on SSO was not successful")
                return None
        except Exception as exc:
            logger.error(f"Error occurred while requesting user info from SSO, {exc}")
            return None
        