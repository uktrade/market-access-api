from unittest import TestCase
from unittest.mock import patch

from django.contrib.auth.models import Group

from api.user.serializers import UserDetailSerializer
from tests.user.factories import UserFactoryMixin


class TestUserDetailSerializer(TestCase, UserFactoryMixin):
    def setUp(self) -> None:
        self.admin_group = Group.objects.get(name="Administrator")
        self.publisher_group = Group.objects.get(name="Publisher")

    @patch("sentry_sdk.capture_message")
    def test_administrator_granted_send_to_sentry(self, mocked_capture_message):
        normal_user = self.create_standard_user()
        serializer = UserDetailSerializer(
            instance=normal_user, data={"groups": [{"id": self.admin_group.id}]}
        )
        assert serializer.is_valid()
        serializer.save()

        assert mocked_capture_message.called_once_with(
            f"User {normal_user.id} has been granted Administrator access"
        )

    @patch("sentry_sdk.capture_message")
    def test_administrator_revoked_send_to_sentry(self, mocked_capture_message):
        admin_user = self.create_admin()
        serializer = UserDetailSerializer(
            instance=admin_user, data={"groups": [{"id": self.publisher_group.id}]}
        )
        assert serializer.is_valid()
        serializer.save()

        assert mocked_capture_message.called_once_with(
            f"User {admin_user.id} has been removed from Administrator group"
        )
