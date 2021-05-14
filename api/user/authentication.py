import base64
from datetime import datetime, timedelta
import logging
import requests
from django.utils.timezone import make_aware
from oauth2_provider.settings import oauth2_settings

from oauth2_provider.oauth2_validators import OAuth2Validator

from django.contrib.auth import get_user_model

from oauth2_provider.models import (
    get_access_token_model,
)
from api.user.staff_sso import sso

log = logging.getLogger(__name__)

AccessToken = get_access_token_model()
USER_MODEL = get_user_model()


class SSOAuthValidator(OAuth2Validator):
    def _get_token_from_authentication_server(
        self, token, introspection_url, introspection_token, introspection_credentials
    ):
        """Override OAuth2Validator user creation function so we can use correct SSO field
        :param introspection_url: introspection endpoint URL
        :param introspection_token: Bearer token
        :param introspection_credentials: Basic Auth credentials (id,secret)
        :return: :class:`models.AccessToken`
        """
        headers = None
        if introspection_token:
            headers = {"Authorization": "Bearer {}".format(introspection_token)}
        elif introspection_credentials:
            client_id = introspection_credentials[0].encode("utf-8")
            client_secret = introspection_credentials[1].encode("utf-8")
            basic_auth = base64.b64encode(client_id + b":" + client_secret)
            headers = {"Authorization": "Basic {}".format(basic_auth.decode("utf-8"))}

        try:
            response = requests.post(
                introspection_url,
                data={"token": token}, headers=headers
            )
        except requests.exceptions.RequestException:
            log.exception("Introspection: Failed POST to %r in token lookup", introspection_url)
            return None

        try:
            content = response.json()
        except ValueError:
            log.exception("Introspection: Failed to parse response as json")
            return None

        if "active" in content and content["active"] is True:
            user, created = USER_MODEL.objects.get_or_create(
                username=content["email_user_id"],
            )

            if created:
                sso_user = sso.get_user_details_by_email_user_id(
                    content["email_user_id"],
                )
                user.email = sso_user["email"]
                user.first_name = sso_user["first_name"]
                user.last_name = sso_user["last_name"]
                user.profile.sso_email_user_id = sso_user["email_user_id"]
                user.profile.sso_user_id = sso_user["user_id"]

                user.save()

            max_caching_time = datetime.now() + timedelta(
                seconds=oauth2_settings.RESOURCE_SERVER_TOKEN_CACHING_SECONDS
            )

            if "exp" in content:
                expires = datetime.utcfromtimestamp(content["exp"])
                if expires > max_caching_time:
                    expires = max_caching_time
            else:
                expires = max_caching_time

            scope = content.get("scope", "")
            expires = make_aware(expires)

            access_token, _created = AccessToken.objects.update_or_create(
                token=token,
                defaults={
                    "user": user,
                    "application": None,
                    "scope": scope,
                    "expires": expires,
                })

            return access_token
