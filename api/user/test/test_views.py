import requests_mock

from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from api.user.staff_sso import StaffSSO


class TestUserView(APITestMixin):
    """User view test case."""

    sso_user_data = {
        "email": "unit.test@unittest.uk",
        "user_id": "907a7a2c-b6cd-454f-3764-a4388ec2a42b",
        "first_name": "Unit",
        "last_name": "Test",
        "related_emails": [
            "unit.test@mocktest.uk"
        ],
        "groups": [],
        "permitted_applications": [
            {
                "key": "app-one",
                "url": "http://undefined",
                "name": "App One"
            },
            {
                "key": "app-two",
                "url": "http://undefined",
                "name": "App Two"
            },
            {
                "key": "app-three",
                "url": "http://undefined",
                "name": "App Three"
            },
        ],
        "access_profiles": [
            "full-access"
        ]
    }

    @patch("api.user.utils.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_authenticated(self, mock_sso_api):
        """Who am I."""

        user_test = create_test_user()
        api_client = self.create_api_client(user=user_test)

        mock_sso_api.return_value = self.sso_user_data

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data["email"]
        assert response_data["username"] == f"{self.sso_user_data['first_name']} {self.sso_user_data['last_name']}"

    @patch("api.user.utils.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_email_as_username(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(username="Testo@Useri.com")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = self.sso_user_data

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data["email"]
        assert response_data["username"] == f"{self.sso_user_data['first_name']} {self.sso_user_data['last_name']}"

    @patch("api.user.utils.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_no_username(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(email="Test.Email@Useri.com", username="")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = self.sso_user_data

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data["email"]
        assert response_data["username"] == f"{self.sso_user_data['first_name']} {self.sso_user_data['last_name']}"

    @patch("api.user.utils.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_no_username_no_email(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(email="", username="")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = self.sso_user_data

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data["email"]
        assert response_data["username"] == f"{self.sso_user_data['first_name']} {self.sso_user_data['last_name']}"

    @patch("api.user.utils.StaffSSO.get_logged_in_user_details")
    def test_who_am_sso_data_none(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(email="Test.Email@Useri.com", username="")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = None

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == "Test.Email@Useri.com"
        assert response_data["username"] == "Test.Email"
        assert response_data["first_name"] == user_test.first_name
        assert response_data["last_name"] == user_test.last_name

    def _test_user_country(self):
        """Test user's country"""

        user_test = create_test_user(location="ba6ee1ca-5d95-e211-a939-e4115bead28a")
        api_client = self.create_api_client(user=user_test)

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            "id": user_test.id,
            "username": user_test.username,
            "last_login": None,
            "first_name": user_test.first_name,
            "last_name": user_test.last_name,
            "email": user_test.email,
            "location": "ba6ee1ca-5d95-e211-a939-e4115bead28a",
            "internal": False,
            "permitted_applications": None,
            "user_profile": None,
        }

    def _test_user_internal(self):
        """Test user's internal flag"""

        user_test = create_test_user(internal=True)
        api_client = self.create_api_client(user=user_test)

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            "id": user_test.id,
            "username": user_test.username,
            "last_login": None,
            "first_name": user_test.first_name,
            "last_name": user_test.last_name,
            "email": user_test.email,
            "location": None,
            "internal": True,
            "permitted_applications": None,
            "user_profile": None,
        }

    def _test_user_profile(self):
        """Test user's internal flag"""
        profile = {
            "internal": False,
            "watch_lists": {
                "watch_list_1": {
                    "country":"955f66a0-5d95-e211-a939-e4115bead28a"
                }
            }
        }
        user_test = create_test_user(user_profile=profile)
        api_client = self.create_api_client(user=user_test)

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            "id": user_test.id,
            "username": user_test.username,
            "last_login": None,
            "first_name": user_test.first_name,
            "last_name": user_test.last_name,
            "email": user_test.email,
            "location": None,
            "internal": False,
            "permitted_applications": None,
            "user_profile": {
                "internal": False,
                "watch_lists": {
                    "watch_list_1": {
                        "country":"955f66a0-5d95-e211-a939-e4115bead28a"
                    }
                }
            },
        }

    def _test_user_edit_add_new_profile(self):
        """Test user's internal flag"""

        user_test = create_test_user(internal=True)
        api_client = self.create_api_client(user=user_test)

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            "id": user_test.id,
            "username": user_test.username,
            "last_login": None,
            "first_name": user_test.first_name,
            "last_name": user_test.last_name,
            "email": user_test.email,
            "location": None,
            "internal": True,
            "permitted_applications": None,
            "user_profile": None,
        }

        edit_response = self.api_client.patch(
            url,
            format="json",
            data={
                "user_profile": {
                    "internal": False,
                    "watch_lists": {
                        "watch_list_1": {
                            "country":"955f66a0-5d95-e211-a939-e4115bead28a"
                        }
                    }
                }
            },
        )

        assert edit_response.status_code == status.HTTP_200_OK

