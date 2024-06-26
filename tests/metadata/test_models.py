from django.test import TestCase

from api.metadata.constants import OrganisationType
from api.metadata.models import BarrierTag, Organisation
from tests.metadata.factories import BarrierTagFactory


class TestBarrierTags(TestCase):
    def test_tag_ordering(self):
        new_tag = BarrierTagFactory()

        last_tag = BarrierTag.objects.last()
        # this is required as we are removing a tag in the
        # middle of the tags list
        assert last_tag.order == new_tag.order

        tags = BarrierTag.objects.all()
        assert tags[0].order == 1
        assert tags[1].order == 2
        assert tags[2].order == 6


class TestOrganisations(TestCase):
    def test_goverment_organisations(self):
        """There should be 24 MD and 3 DA - correct as of Mar 2023"""
        md_qs = Organisation.objects.filter(
            organisation_type=OrganisationType.MINISTERIAL_DEPARTMENTS
        )
        da_qs = Organisation.objects.filter(
            organisation_type=OrganisationType.DEVOLVED_ADMINISTRATIONS
        )

        assert 28 == md_qs.count()
        assert 3 == da_qs.count()
