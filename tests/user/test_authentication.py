import base64
from datetime import datetime, timedelta
from unittest.case import TestCase

import pytest
import requests
from django.contrib.auth import get_user_model
from mock import patch
from oauth2_provider.models import get_access_token_model

from api.user.authentication import SSOAuthValidator
from tests.user.factories import UserFactoryMixin

AccessToken = get_access_token_model()
USER_MODEL = get_user_model()

pytestmark = [pytest.mark.django_db]


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class TestSSOValidator(TestCase, UserFactoryMixin):
    def setUp(self):
        self.validator = SSOAuthValidator()

        self.test_user = self.create_standard_user()

        assert self.test_user.last_login is None

        self.sso_user = {
            "email": "sso_email",
            "contact_email": "contact_email",
            "first_name": "sso_first_name",
            "last_name": "sso_last_name",
            "email_user_id": "sso_email_user_id",
            "user_id": self.test_user.id,
        }

        self.expiry_datetime = datetime.now() + timedelta(days=2)
        self.timestamp = self.expiry_datetime.timestamp()

    def test_handle_header_token(self):
        response = self.validator._handle_header("token_goes_here", "")

        expected_header = {"Authorization": "Bearer token_goes_here"}
        assert response == expected_header

    def test_handle_header_credentials(self):
        response = self.validator._handle_header(
            "", ["id_goes_here", "secret_goes_here"]
        )

        expected_encode = base64.b64encode(
            "id_goes_here".encode("utf-8")
            + ":".encode("utf-8")
            + "secret_goes_here".encode("utf-8")
        ).decode("utf-8")
        expected_header = {"Authorization": f"Basic {expected_encode}"}
        assert response == expected_header

    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_email_user_id")
    def test_handle_auth_new_user(self, mock_sso_user):
        content = {"email_user_id": "id_goes_here"}
        mock_sso_user.return_value = self.sso_user

        response = self.validator._handle_auth_user(content)

        mock_sso_user.assert_called_with("id_goes_here")
        assert response.email == self.sso_user["contact_email"]
        assert response.first_name == self.sso_user["first_name"]
        assert response.last_name == self.sso_user["last_name"]
        assert response.profile.sso_email_user_id == self.sso_user["email_user_id"]
        assert response.profile.sso_user_id == self.sso_user["user_id"]

    @patch("api.user.staff_sso.StaffSSO.get_user_details_by_email_user_id")
    def test_handle_auth_existing_user(self, mock_sso_user):
        content = {"email_user_id": self.test_user.username}
        mock_sso_user.return_value = self.sso_user
        response = self.validator._handle_auth_user(content)

        mock_sso_user.assert_called_with(self.test_user.username)
        assert response.last_login is not None
        assert response.email == self.sso_user["contact_email"]
        assert response.first_name == self.test_user.first_name
        assert response.last_name == self.test_user.last_name
        assert (
            response.profile.sso_email_user_id
            == self.test_user.profile.sso_email_user_id
        )
        assert response.profile.sso_user_id == self.test_user.profile.sso_user_id

    @patch("requests.post")
    @patch("api.user.authentication.SSOAuthValidator._handle_header")
    @patch("api.user.authentication.SSOAuthValidator._handle_auth_user")
    def test_get_token(self, mock_handle_auth_user, mock_handle_header, mock_post):
        mock_post.return_value = MockResponse(
            json_data={"active": True, "exp": self.timestamp}, status_code=200
        )

        mock_handle_auth_user.return_value = self.test_user

        response = self.validator._get_token_from_authentication_server(
            "token123",
            "an_introspection_url",
            "an_introspection_token",
            "",
        )

        mock_handle_header.assert_called_with("an_introspection_token", "")
        mock_handle_auth_user.assert_called_with(
            {"active": True, "exp": self.timestamp}
        )
        assert type(response) == AccessToken
        assert response.token == "token123"
        assert response.user_id == self.test_user.id

        # This test checks the expiry date of the returned token does not exceed the max allowed time
        assert response.expires != self.expiry_datetime

    @patch("requests.post")
    @patch("api.user.authentication.SSOAuthValidator._handle_header")
    @patch("logging.Logger.exception")
    def test_get_token_failed_token(self, mock_log, mock_handle_header, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Fail here")

        response = self.validator._get_token_from_authentication_server(
            "token123",
            "an_introspection_url",
            "an_introspection_token",
            "",
        )

        mock_handle_header.assert_called_with("an_introspection_token", "")
        mock_log.assert_called_with(
            "Introspection: Failed POST to %r in token lookup", "an_introspection_url"
        )

        assert response is None

    @patch("requests.post")
    @patch("api.user.authentication.SSOAuthValidator._handle_header")
    @patch("logging.Logger.exception")
    @patch("tests.user.test_authentication.MockResponse.json")
    def test_get_token_invalid_response(
        self, mock_json, mock_log, mock_handle_header, mock_post
    ):
        mock_post.return_value = MockResponse(
            json_data={"Give it invalid JSON"}, status_code=200
        )

        mock_json.side_effect = ValueError

        response = self.validator._get_token_from_authentication_server(
            "token123",
            "an_introspection_url",
            "an_introspection_token",
            "",
        )

        mock_handle_header.assert_called_with("an_introspection_token", "")
        mock_log.assert_called_with("Introspection: Failed to parse response as json")

        assert response is None

    @patch("requests.post")
    @patch("api.user.authentication.SSOAuthValidator._handle_header")
    @patch("api.user.authentication.SSOAuthValidator._handle_auth_user")
    def test_get_token_inactive_user(
        self, mock_handle_auth_user, mock_handle_header, mock_post
    ):
        mock_post.return_value = MockResponse(
            json_data={"active": False, "exp": self.timestamp}, status_code=200
        )

        mock_handle_auth_user.return_value = self.test_user

        response = self.validator._get_token_from_authentication_server(
            "token123",
            "an_introspection_url",
            "an_introspection_token",
            "",
        )

        mock_handle_header.assert_called_with("an_introspection_token", "")
        mock_handle_auth_user.assert_not_called()
        assert response is None

    @patch("requests.post")
    @patch("api.user.authentication.SSOAuthValidator._handle_header")
    @patch("api.user.authentication.SSOAuthValidator._handle_auth_user")
    def test_get_token_missing_active_content(
        self, mock_handle_auth_user, mock_handle_header, mock_post
    ):
        mock_post.return_value = MockResponse(
            json_data={"active": None, "exp": self.timestamp}, status_code=200
        )

        mock_handle_auth_user.return_value = self.test_user

        response = self.validator._get_token_from_authentication_server(
            "token123",
            "an_introspection_url",
            "an_introspection_token",
            "",
        )

        mock_handle_header.assert_called_with("an_introspection_token", "")
        mock_handle_auth_user.assert_not_called()
        assert response is None
