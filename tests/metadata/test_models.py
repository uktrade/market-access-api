from django.test import TestCase

from api.metadata.models import BarrierTag
from tests.metadata.factories import BarrierTagFactory


class TestBarrierTags(TestCase):

    def test_tag_ordering(self):
        # we have 2 default tags already in migrations
        # so let's add a third
        tag3 = BarrierTagFactory()

        assert 3 == BarrierTag.objects.count()
        assert 3 == tag3.order

        tags = BarrierTag.objects.all()
        assert 1 == tags[0].order
        assert 2 == tags[1].order
        assert 3 == tags[2].order
