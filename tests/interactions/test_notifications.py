from http import HTTPStatus
from unittest.mock import patch

import pytest
from api.barriers.models import Barrier, PublicBarrier
from api.interactions.models import (
    ExcludeFromNotifications,
    Interaction,
    Mention,
    PublicBarrierNote,
    _get_mentions,
    _handle_mention_notification,
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


class NotificationSetUp(BaseNotificationTestCase):
    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user("foo", "foo@test.gov.uk", "bar")
        self.user2 = User.objects.create_user("foo2", "foo2@test.gov.uk", "bar2")
        self.user3 = User.objects.create_user("foo3", "foo3@test.gov.uk", "bar3")

        self.mock_barrier = Barrier()
        self.mock_barrier.code = "example code"
        self.mock_barrier.title = "example title"
        self.mock_barrier.created_by = self.user
        self.mock_barrier.save()


class TestPublicBarrierNotification(NotificationSetUp):
    count = 1

    def setUp(self):
        super().setUp()
        self.mock_pub_bar = PublicBarrier.objects.get(barrier=self.mock_barrier)

    def test_single_mention_publicbarriernote(self):
        text = "test mention @foo@test.gov.uk"
        publicbarriernote = PublicBarrierNote(
            created_by=self.user,
            public_barrier=self.mock_pub_bar,
            text=text,
        )

        assert Mention.objects.filter().exists() is False
        publicbarriernote.save()
        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 1

    def test_many_mentions_publicbarriernote(self):
        text = "test mention @foo@test.gov.uk, @foo2@test.gov.uk, @foo3@test.gov.uk"
        publicbarriernote = PublicBarrierNote(
            created_by=self.user,
            public_barrier=self.mock_pub_bar,
            text=text,
        )

        assert Mention.objects.filter().exists() is False
        publicbarriernote.save()
        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 3

    def test_excluded_emails_should_still_create_mentions(self):
        excluded = ExcludeFromNotifications.objects.create(
            excluded_user=self.user2,
            exclude_email=self.user2.email,
            created_by=self.user2,
            modified_by=self.user2,
        )
        text = "test mention @foo@test.gov.uk, @foo2@test.gov.uk, @foo3@test.gov.uk"
        publicbarriernote = PublicBarrierNote(
            created_by=self.user,
            public_barrier=self.mock_pub_bar,
            text=text,
        )

        assert Mention.objects.filter().exists() is False
        publicbarriernote.save()
        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 3


class TestInteractionNotification(NotificationSetUp):
    def test_single_mention_interaction(self):
        text = "test mention @foo@test.gov.uk"
        interaction = Interaction(
            created_by=self.user,
            barrier=self.mock_barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )

        assert Mention.objects.filter().exists() is False
        interaction.save()
        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 1

    def test_many_mentions_interaction(self):
        text = "test mention @foo@test.gov.uk, @foo2@test.gov.uk, @foo3@test.gov.uk"
        interaction = Interaction(
            created_by=self.user,
            barrier=self.mock_barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )

        assert Mention.objects.filter().exists() is False
        interaction.save()
        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 3

    def test_exclude_mentions_interaction(self):
        excluded = ExcludeFromNotifications.objects.create(
            excluded_user=self.user2,
            exclude_email=self.user2.email,
            created_by=self.user2,
            modified_by=self.user2,
        )
        text = "test mention @foo@test.gov.uk, @foo2@test.gov.uk, @foo3@test.gov.uk"
        interaction = Interaction(
            created_by=self.user,
            barrier=self.mock_barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )

        assert Mention.objects.filter().exists() is False
        interaction.save()
        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 3


class TestMentionNotification(NotificationSetUp):
    def test_one_notification(self):
        text = "test mention @foo@test.gov.uk"
        assert Mention.objects.filter().exists() is False

        interaction = Interaction(
            created_by=self.user,
            barrier=self.mock_barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )

        _handle_mention_notification(interaction, self.mock_barrier, self.user)

        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 1

    def test_many_notification(self):
        text = "test mention @foo@test.gov.uk, @foo2@test.gov.uk, @foo3@test.gov.uk"
        assert Mention.objects.filter().exists() is False

        interaction = Interaction(
            created_by=self.user,
            barrier=self.mock_barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )

        _handle_mention_notification(interaction, self.mock_barrier, self.user)

        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 3

    @pytest.mark.skip()
    def test_exclude_notification(self):
        excluded = ExcludeFromNotifications.objects.create(
            excluded_user=self.user2,
            exclude_email=self.user2.email,
            created_by=self.user2,
            modified_by=self.user2,
        )
        text = "test mention @foo@test.gov.uk, @foo2@test.gov.uk, @foo3@test.gov.uk"
        assert Mention.objects.filter().exists() is False

        interaction = Interaction(
            created_by=self.user,
            barrier=self.mock_barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )

        _handle_mention_notification(interaction, self.mock_barrier, self.user)

        assert Mention.objects.filter().exists() is True
        assert Mention.objects.filter().count() == 3


class TestRemoveExcluded(BaseNotificationTestCase):
    def test_exclude(self):
        # NB: email format is not checked
        user1 = User.objects.create_user("foo1", "foo1@test.com", "bar1")
        user2 = User.objects.create_user("foo2", "foo2@test.com", "bar3")
        user3 = User.objects.create_user("foo3", "foo3@test.com", "bar3")

        excluded1 = ExcludeFromNotifications.objects.create(
            excluded_user=user1,
            exclude_email=user1.email,
            created_by=user1,
            modified_by=user1,
        )
        excluded2 = ExcludeFromNotifications.objects.create(
            excluded_user=user2,
            exclude_email=user2.email,
            created_by=user2,
            modified_by=user2,
        )
        excluded3 = ExcludeFromNotifications.objects.create(
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
@good2@digital.trade.gov.uk"""  # noqa

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
        data = (
            "@good1@trade.gov.uk and @good1@trade.gov.uk and @good1@trade.gov.uk and "
            "@good2@trade.gov.uk and @good2@trade.gov.uk"
        )
        expected = ["good1@trade.gov.uk", "good2@trade.gov.uk"]
        res = _get_mentions(data)
        assert res == expected


class TestExcludeNotifcationREST(BaseNotificationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mentions-exclude-from-notifications")
        self.user = User.objects.create_user("foo", "myemail@test.com", "bar")
        self.client.login(username="foo", password="bar")

    @pytest.mark.skip()
    def test_exclude_notifcation(self):
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).exists()
            is False
        )

        res = self.client.post(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).count()
            == 1
        )

        # Show that repeated calls do not create repeated DB rows
        res = self.client.post(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).count()
            == 1
        )

    @pytest.mark.skip()
    def test_remove_from_exclude_notification(self):
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).exists()
            is False
        )
        excluded = ExcludeFromNotifications.objects.create(
            excluded_user=self.user,
            exclude_email=self.user.email,
            created_by=self.user,
            modified_by=self.user,
        )
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).exists()
            is True
        )
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).count()
            == 1
        )

        res = self.client.delete(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).exists()
            is False
        )
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).count()
            == 0
        )

        # show that repeated calls to delete an exclusion does not cause an error
        res = self.client.delete(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).exists()
            is False
        )
        assert (
            ExcludeFromNotifications.objects.filter(excluded_user=self.user).count()
            == 0
        )
