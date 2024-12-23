from logging import getLogger
from unittest.mock import patch

import freezegun
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from tests.user.factories import UserFactoryMixin

logger = getLogger(__name__)

freezegun.configure(extend_ignore_list=["transformers"])


class TestUserView(APITestMixin, UserFactoryMixin):
    """User view test case."""

    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_authenticated(self, mock_sso_api):
        """Who am I."""

        user_test = create_test_user()
        api_client = self.create_api_client(user=user_test)

        mock_sso_api.return_value = self.sso_user_data_1

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data_1["email"]
        assert (
            response_data["username"] == f"{user_test.first_name} {user_test.last_name}"
        )

    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_email_as_username(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(username="Testo@Useri.com")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = self.sso_user_data_1

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data_1["email"]
        assert (
            response_data["username"] == f"{user_test.first_name} {user_test.last_name}"
        )

    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_no_username(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(email="Test.Email@Useri.com", username="")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = self.sso_user_data_1

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data_1["email"]
        assert (
            response_data["username"] == f"{user_test.first_name} {user_test.last_name}"
        )

    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
    def test_who_am_i_no_username_no_email(self, mock_sso_api):
        """Who am I, when email is set in username"""

        user_test = create_test_user(email="", username="")
        api_client = self.create_api_client(user=user_test)
        mock_sso_api.return_value = self.sso_user_data_1

        url = reverse("who_am_i")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["email"] == self.sso_user_data_1["email"]
        assert (
            response_data["username"] == f"{user_test.first_name} {user_test.last_name}"
        )

    @patch("api.user.staff_sso.StaffSSO.get_logged_in_user_details")
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
        assert (
            response_data["username"] == f"{user_test.first_name} {user_test.last_name}"
        )
        assert response_data["first_name"] == user_test.first_name
        assert response_data["last_name"] == user_test.last_name

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    def test_user_country(self):
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

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    def test_user_internal(self):
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

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    def test_user_profile(self):
        """Test user's internal flag"""
        profile = {
            "internal": False,
            "watch_lists": {
                "watch_list_1": {"country": "955f66a0-5d95-e211-a939-e4115bead28a"}
            },
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
                    "watch_list_1": {"country": "955f66a0-5d95-e211-a939-e4115bead28a"}
                },
            },
        }

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    def test_user_edit_add_new_profile(self):
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
                            "country": "955f66a0-5d95-e211-a939-e4115bead28a"
                        }
                    },
                }
            },
        )

        assert edit_response.status_code == status.HTTP_200_OK

    # pytest tests/user/test_views.py::TestUserView::test_update_protected_user_detail_admin
    def test_update_protected_user_detail_admin(self):
        """
        Attempting to update a user profiles protected fields will pass with
        admin permissions.
        """
        update_user_test = self.create_standard_user()
        admin_user_test = self.create_admin()
        api_client = self.create_api_client(user=admin_user_test)

        url = f"{reverse('user-list')}/{update_user_test.id}"

        pre_test_groups = update_user_test.groups.all()
        assert len(pre_test_groups) == 0

        edit_protected_response = api_client.patch(
            url,
            format="json",
            data={"groups": [{"id": "4"}]},
        )

        assert edit_protected_response.status_code == 200

        post_test_groups = update_user_test.groups.all()
        assert len(post_test_groups) == 1
        assert update_user_test.groups.filter(name="Administrator").exists()

    def test_update_protected_user_detail_denied_permission(self):
        """
        Attempting to update a user profiles protected fields without admin
        permissions will reject the request.
        """
        update_user_test = self.create_standard_user()
        api_client = self.create_api_client(user=update_user_test)

        url = f"{reverse('user-list')}/{update_user_test.id}"

        pre_test_groups = update_user_test.groups.all()
        assert len(pre_test_groups) == 0

        edit_protected_response = api_client.patch(
            url,
            format="json",
            data={"groups": [{"id": "4"}]},
        )

        assert edit_protected_response.status_code == 403

        post_test_groups = update_user_test.groups.all()
        assert len(post_test_groups) == 0
