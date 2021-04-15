from django.test import TestCase
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import OrganisationFactory


class TestBarrierModel(TestCase):
    def test_caused_by_trading_bloc_clears_on_non_trading_bloc_country(self):
        barrier = BarrierFactory(
            country="82756b9a-5d95-e211-a939-e4115bead28a",
            caused_by_trading_bloc=True,
        )
        assert barrier.country == "82756b9a-5d95-e211-a939-e4115bead28a"
        assert barrier.caused_by_trading_bloc is True

        barrier.country = "81756b9a-5d95-e211-a939-e4115bead28a"
        barrier.save()

        assert barrier.country == "81756b9a-5d95-e211-a939-e4115bead28a"
        assert barrier.caused_by_trading_bloc is None

    def test_barrier_government_organisations(self):
        org1 = OrganisationFactory()
        org2 = OrganisationFactory(organisation_type=1000)
        barrier = BarrierFactory()
        barrier.organisations.add(org1, org2)

        assert 2 == barrier.organisations.count()
        assert 1 == barrier.government_organisations.count()
        assert org1 == barrier.government_organisations.first()
        assert org2 not in barrier.government_organisations.all()
