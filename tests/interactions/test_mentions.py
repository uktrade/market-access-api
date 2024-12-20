from datetime import datetime

import freezegun
from django.urls import reverse
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin
from api.interactions.models import Mention
from tests.barriers.factories import BarrierFactory

freezegun.configure(extend_ignore_list=["transformers"])


class TestMentionCounts(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mentions-counts")

    def test_get_mention_counts_no_mentions(self):
        response = self.api_client.get(self.url)

        assert response.data == {"read_by_recipient": 0, "total": 0}

    def test_get_mention_counts_with_mentions(self):
        barrier = BarrierFactory()
        Mention.objects.create(recipient=self.user, barrier=barrier)
        Mention.objects.create(
            recipient=self.user, barrier=barrier, read_by_recipient=True
        )

        response = self.api_client.get(self.url)

        assert response.data == {"read_by_recipient": 1, "total": 2}

    def test_old_mentions_not_included_in_count(self):
        barrier = BarrierFactory()
        Mention.objects.create(recipient=self.user, barrier=barrier)
        Mention.objects.create(
            recipient=self.user, barrier=barrier, read_by_recipient=True
        )

        ts = datetime(2022, 10, 15, 12, 0, 1)

        with freezegun.freeze_time(ts):
            Mention.objects.create(recipient=self.user, barrier=barrier)

        response = self.api_client.get(self.url)

        assert response.data == {"read_by_recipient": 1, "total": 2}
