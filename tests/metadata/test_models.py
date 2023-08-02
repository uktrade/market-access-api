from django.test import TestCase

from api.metadata.constants import OrganisationType
from api.metadata.models import BarrierTag, Organisation
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


class TestOrganisations(TestCase):
    def test_goverment_organisations(self):
        """There should be 24 MD and 3 DA - correct as of Mar 2023"""
        md_qs = Organisation.objects.filter(
            organisation_type=OrganisationType.MINISTERIAL_DEPARTMENTS
        )
        da_qs = Organisation.objects.filter(
            organisation_type=OrganisationType.DEVOLVED_ADMINISTRATIONS
        )

        assert 24 == md_qs.count()
        assert 3 == da_qs.count()
