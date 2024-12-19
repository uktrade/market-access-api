from django.urls import reverse
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin
from api.interactions.models import Mention
from tests.barriers.factories import BarrierFactory


class TestMentionCounts(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mentions-counts")

    def test_get_mention_counts_no_mentions(self):
        response = self.api_client.get(self.url)

        assert response.data == {
            "read_by_recipient": 0,
            "total": 0
        }

    def test_get_mention_counts_with_mentions(self):
        barrier = BarrierFactory()
        Mention.objects.create(
            recipient=self.user,
            barrier=barrier
        )
        Mention.objects.create(
            recipient=self.user,
            barrier=barrier,
            read_by_recipient=True
        )

        response = self.api_client.get(self.url)

        assert response.data == {
            "read_by_recipient": 1,
            "total": 2
        }
