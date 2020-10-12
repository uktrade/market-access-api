from django.test import TestCase

from api.metadata.models import BarrierTag
from tests.metadata.factories import BarrierTagFactory


class TestBarrierTags(TestCase):

    def test_tag_ordering(self):
        new_tag = BarrierTagFactory()

        tag_count = BarrierTag.objects.count()
        assert tag_count == new_tag.order

        tags = BarrierTag.objects.all()
        assert 1 == tags[0].order
        assert 2 == tags[1].order
        assert 3 == tags[2].order
