from unittest import TestCase
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group

from api.user.serializers import UserDetailSerializer
from tests.user.factories import UserFactoryMixin

pytestmark = [pytest.mark.django_db]


class TestUserDetailSerializer(TestCase, UserFactoryMixin):
    def setUp(self) -> None:
        self.admin_group = Group.objects.get(name="Administrator")
        self.publisher_group = Group.objects.get(name="Publisher")
        self.analyst_group = Group.objects.get(name="Analyst")
        self.approver_group = Group.objects.get(name="Public barrier approver")

    @patch("logging.Logger.critical")
    def test_administrator_granted_critical_log(self, patched_logger):
        normal_user = self.create_standard_user()
        serializer = UserDetailSerializer(
            instance=normal_user,
            partial=True,
            data={"groups": [{"id": self.admin_group.id}]},
        )
        assert serializer.is_valid()
        serializer.save()

        assert patched_logger.called_once_with(
            f"User {normal_user.id} has been granted Administrator access"
        )

    @patch("logging.Logger.critical")
    def test_administrator_revoked_send_to_sentry(self, patched_logger):
        admin_user = self.create_admin()
        serializer = UserDetailSerializer(
            instance=admin_user,
            partial=True,
            data={"groups": [{"id": self.publisher_group.id}]},
        )
        assert serializer.is_valid()
        serializer.save()

        assert patched_logger.called_once_with(
            f"User {admin_user.id} has been removed from Administrator group"
        )

    @patch("logging.Logger.info")
    def test_group_modifications_logged(self, patched_logger):
        admin_user = self.create_approver()

        serializer = UserDetailSerializer(
            instance=admin_user,
            partial=True,
            data={"groups": [{"id": self.publisher_group.id}]},
        )
        assert serializer.is_valid()
        serializer.save()

        assert patched_logger.call_count == 2
        assert patched_logger.called_with(
            "User 5 has been added to the following groups: {'Publisher'}"
        )
        assert patched_logger.called_with(
            "User 5 has been removed from the following groups: {'Public barrier approver'}"
        )
