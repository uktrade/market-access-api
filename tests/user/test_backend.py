import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from api.user.backend import CustomAuthbrokerBackend

User = get_user_model()


class TestCustomAuthbrokerBackend(TestCase):
    def setUp(self):
        user_id = uuid.uuid4()
        self.mock_raw_profile = {
            "user_id": user_id,
            "email_user_id": f"first-{user_id}-last@trade.gov.uk",
            "contact_email": "first-last@trade.gov.uk",
            "email": "first-last@trade.gov.uk",
            "first_name": "first",
            "last_name": "last",
        }

    def test_build_profile(self):
        user = User()
        user.save()
        profile_data = user.profile

        profile_data.sso_user_id != self.mock_raw_profile["user_id"]
        profile_data.sso_email_user_id != self.mock_raw_profile["email_user_id"]
        profile_data.user.email != self.mock_raw_profile.get("contact_email")
        # contact emails ?
        profile_data.user.first_name != self.mock_raw_profile[
            "first_name"
        ]  # might change over time
        profile_data.user.last_name != self.mock_raw_profile[
            "last_name"
        ]  # might change over time
        profile_data.user.username != self.mock_raw_profile["email_user_id"]

        CustomAuthbrokerBackend._build_profile(
            profile_data, self.mock_raw_profile["email"], self.mock_raw_profile
        )

        profile_data.sso_user_id == self.mock_raw_profile["user_id"]
        profile_data.sso_email_user_id == self.mock_raw_profile["email_user_id"]
        profile_data.user.email == self.mock_raw_profile.get("contact_email")
        # contact emails ?
        profile_data.user.first_name == self.mock_raw_profile[
            "first_name"
        ]  # might change over time
        profile_data.user.last_name == self.mock_raw_profile[
            "last_name"
        ]  # might change over time
        profile_data.user.username == self.mock_raw_profile["email_user_id"]  #

    def test_verify_user_object(self):
        user = CustomAuthbrokerBackend.verify_user_object(self.mock_raw_profile)

        user.first_name == self.mock_raw_profile["first_name"]  # might change over time
        user.last_name == self.mock_raw_profile["last_name"]  # might change over time
        user.username == self.mock_raw_profile["email_user_id"]
        user.profile.sso_user_id == self.mock_raw_profile["user_id"]
        user.profile.sso_email_user_id == self.mock_raw_profile["email_user_id"]
        user.profile.user.email == self.mock_raw_profile.get("contact_email")
