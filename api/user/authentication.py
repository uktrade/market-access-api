import base64
import logging
from datetime import datetime, timedelta

import requests
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from oauth2_provider.models import get_access_token_model
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.settings import oauth2_settings

from api.user.staff_sso import sso

log = logging.getLogger(__name__)

AccessToken = get_access_token_model()
USER_MODEL = get_user_model()


class SSOAuthValidator(OAuth2Validator):
    def _handle_header(self, introspection_token, introspection_credentials):
        headers = None
        if introspection_token:
            headers = {"Authorization": "Bearer {}".format(introspection_token)}
        elif introspection_credentials:
            client_id = introspection_credentials[0].encode("utf-8")
            client_secret = introspection_credentials[1].encode("utf-8")
            basic_auth = base64.b64encode(client_id + b":" + client_secret)
            headers = {"Authorization": "Basic {}".format(basic_auth.decode("utf-8"))}

        return headers

    def _handle_auth_user(self, content):
        user, created = USER_MODEL.objects.get_or_create(
            username=content["email_user_id"],
        )

        sso_user = sso.get_user_details_by_email_user_id(
            content["email_user_id"],
        )

        if created:
            user.email = sso_user["email"]
            user.first_name = sso_user["first_name"]
            user.last_name = sso_user["last_name"]
            user.profile.sso_email_user_id = sso_user["email_user_id"]
            user.profile.sso_user_id = sso_user["user_id"]
            user.save()
        else:
            if sso_user and user.email != sso_user["email"]:
                user.email = sso_user["email"]
                user.save()

        return user

    def _get_token_from_authentication_server(
        self, token, introspection_url, introspection_token, introspection_credentials
    ):
        """Override OAuth2Validator user creation function so we can use correct SSO field
        :param introspection_url: introspection endpoint URL
        :param introspection_token: Bearer token
        :param introspection_credentials: Basic Auth credentials (id,secret)
        :return: :class:`models.AccessToken`
        """
        headers = self._handle_header(introspection_token, introspection_credentials)

        try:
            response = requests.post(
                introspection_url, data={"token": token}, headers=headers
            )
        except requests.exceptions.RequestException:
            log.exception(
                "Introspection: Failed POST to %r in token lookup", introspection_url
            )
            return None

        try:
            content = response.json()
        except ValueError:
            log.exception("Introspection: Failed to parse response as json")
            return None

        if not content["active"]:
            return None

        if "active" not in content:
            return None

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
        user = self._handle_auth_user(content)

        access_token, _created = AccessToken.objects.update_or_create(
            token=token,
            defaults={
                "user": user,
                "application": None,
                "scope": scope,
                "expires": expires,
            },
        )

        return access_token
