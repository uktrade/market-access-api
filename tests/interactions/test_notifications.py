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


class BaseNotificationTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.patch_notify = patch("api.interactions.models.NotificationsAPIClient")
        self.mock_notify = self.patch_notify.start()

    def tearDown(self):
        self.patch_notify.stop()
        super().tearDown()


class TestRemoveExcluded(BaseNotificationTestCase):
    def test_exclude(self):
        # NB: email format is not checked
        user1 = User.objects.create_user("foo1", "foo1@test.com", "bar1")
        user2 = User.objects.create_user("foo2", "foo2@test.com", "bar3")
        user3 = User.objects.create_user("foo3", "foo3@test.com", "bar3")

        excluded1 = ExcludeFromNotifcation.objects.create(
            excluded_user=user1,
            exclude_email=user1.email,
            created_by=user1,
            modified_by=user1,
        )
        excluded2 = ExcludeFromNotifcation.objects.create(
            excluded_user=user2,
            exclude_email=user2.email,
            created_by=user2,
            modified_by=user2,
        )
        excluded3 = ExcludeFromNotifcation.objects.create(
            excluded_user=user3,
            exclude_email=user3.email,
            created_by=user3,
            modified_by=user3,
        )

        data = ["foo2@test.com", "foo3@test.com", "foo4@test.com", "foo5@test.com"]
        expected = ["foo4@test.com", "foo5@test.com"]
        res = _remove_excluded(data)
        assert res == expected


class TestGetMentions(BaseNotificationTestCase):
    def test_get_mentions_regex(self):
        data = """
This is an example test for bad1@value.gov.uk and @bad2@value.com with @bad4@trade.uk
those 3 values should fail. The working example should be @good.name@nosuch.dept.gov.uk
@good.first.name@trade.gov.uk and @goodish@very.many.many.vhosts.for.this.test.gov.uk and this @good.first.third.name@gov.uk and some words
@good1@digital.trade.gov.uk
@good2@digital.trade.gov.uk"""

        expected = sorted(
            [
                "good.name@nosuch.dept.gov.uk",
                "good.first.name@trade.gov.uk",
                "goodish@very.many.many.vhosts.for.this.test.gov.uk",
                "good.first.third.name@gov.uk",
                "good1@digital.trade.gov.uk",
                "good2@digital.trade.gov.uk",
            ]
        )
        res = _get_mentions(data)
        assert res == expected

    def test_single_mention(self):
        data = "@good@trade.gov.uk"
        expected = ["good@trade.gov.uk"]
        res = _get_mentions(data)
        assert res == expected

    def test_no_mentions(self):
        data = "there are no mentions here"
        expected = []
        res = _get_mentions(data)
        assert res == expected

    def test_dedupe_mentions(self):
        data = "@good1@trade.gov.uk and @good1@trade.gov.uk and @good1@trade.gov.uk and @good2@trade.gov.uk and @good2@trade.gov.uk"
        expected = ["good1@trade.gov.uk", "good2@trade.gov.uk"]
        res = _get_mentions(data)
        assert res == expected


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
