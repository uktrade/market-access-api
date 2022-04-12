from django.test import TestCase

from api.barriers.models import Barrier
from api.barriers.signals.handlers import barrier_completion_percentage_changed
from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory, CommodityFactory
from tests.metadata.factories import CategoryFactory


class TestSignalFunctions(APITestMixin, TestCase):
    def test_barrier_completion_percentage_changed_full(self):
        barrier = BarrierFactory(
            country="a05f66a0-5d95-e211-a939-e4115bead28a",
            summary="This... Is... A SUMMARY!",
            source="Ketchup",
            sectors=["75debee7-a182-410e-bde0-3098e4f7b822"],
        )
        category = CategoryFactory()
        barrier.categories.add(category)
        barrier.commodities.set((CommodityFactory(code="010410"),))
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 100

    def test_barrier_completion_percentage_changed_none(self):
        barrier = Barrier()
        barrier.save()

        barrier.refresh_from_db()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        assert barrier.completion_percent == 0

    def test_barrier_completion_percentage_changed_location_only(self):
        barrier = Barrier()
        barrier.country = "a05f66a0-5d95-e211-a939-e4115bead28a"
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 18

    def test_barrier_completion_percentage_changed_summary_only(self):
        barrier = Barrier()
        barrier.summary = "This... Is... A SUMMARY!"
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 18

    def test_barrier_completion_percentage_changed_source_only(self):
        barrier = Barrier()
        barrier.source = "Ketchup"
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 16

    def test_barrier_completion_percentage_changed_sector_only(self):
        barrier = Barrier()
        barrier.sectors = ["75debee7-a182-410e-bde0-3098e4f7b822"]
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 16

    def test_barrier_completion_percentage_changed_category_only(self):
        barrier = Barrier()
        barrier.save()

        category = CategoryFactory()
        barrier.categories.add(category)
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 16

    def test_barrier_completion_percentage_changed_commodity_only(self):
        barrier = Barrier()
        barrier.save()

        barrier.commodities.set((CommodityFactory(code="010410"),))
        barrier.save()

        barrier_completion_percentage_changed(sender=Barrier, instance=barrier)

        barrier.refresh_from_db()

        assert barrier.completion_percent == 16
