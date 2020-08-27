from django.test import TestCase

from tests.barriers.factories import BarrierFactory


class TestBarrierModel(TestCase):

    def test_caused_by_trading_bloc_clears_on_non_trading_bloc_country(self):
        barrier = BarrierFactory(
            export_country="82756b9a-5d95-e211-a939-e4115bead28a",
            caused_by_trading_bloc=True,
        )
        assert barrier.export_country == "82756b9a-5d95-e211-a939-e4115bead28a"
        assert barrier.caused_by_trading_bloc is True

        barrier.export_country = "b05f66a0-5d95-e211-a939-e4115bead28a"
        barrier.save()

        assert barrier.export_country == "b05f66a0-5d95-e211-a939-e4115bead28a"
        assert barrier.caused_by_trading_bloc is None
