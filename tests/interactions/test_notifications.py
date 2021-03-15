from http import HTTPStatus
from unittest.mock import patch

from api.interactions.models import (
    ExcludeFromNotifcation,
    Interaction,
    PublicBarrierNote,
    _get_mentions,
    _handle_tagged_users,
    _remove_excluded,
)
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.reverse import reverse


class TestExcludeNotifcationREST(TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mentions-mark-as-read")
        self.user = User.objects.create_user("foo", "myemail@test.com", "bar")
        self.client.login(username="foo", password="bar")

    def test_exclude_notifcation(self):
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )

        res = self.client.post(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 1
        )

        # Show that repeated calls do not create repeated DB rows
        res = self.client.post(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 1
        )

    def test_remove_from_exclude_notification(self):
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )
        excluded = ExcludeFromNotifcation.objects.create(
            excluded_user=self.user,
            exclude_email=self.user.email,
            created_by=self.user,
            modified_by=self.user,
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is True
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 1
        )

        res = self.client.delete(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 0
        )

        # show that repeated calls to delete an exclusion does not cause an error
        res = self.client.delete(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 0
        )
