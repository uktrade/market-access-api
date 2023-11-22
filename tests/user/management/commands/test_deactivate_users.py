from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from api.core.test_utils import create_test_user


class TestFixAllUsers(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        # self.helper_sso_patch.stop()
        super().tearDown()

    def test_deactivate_users(self):
        user1 = create_test_user()
        user2 = create_test_user()
        user3 = create_test_user()

        assert user1.is_active
        assert user2.is_active
        assert user3.is_active

        UserModel = get_user_model()

        assert UserModel.objects.all().count() == 3
        assert UserModel.objects.filter(is_active=True).count() == 3

        emails = [user1.email, user2.email]

        call_command("deactivate_users", emails=",".join(emails))

        assert UserModel.objects.all().count() == 3
        assert UserModel.objects.filter(is_active=True).count() == 1

        user1.refresh_from_db()
        user2.refresh_from_db()
        user3.refresh_from_db()

        assert not user1.is_active
        assert not user2.is_active
        assert user3.is_active
