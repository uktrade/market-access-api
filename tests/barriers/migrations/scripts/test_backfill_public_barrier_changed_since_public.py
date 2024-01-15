from django.db.models import signals
from django.apps import apps

from api.barriers.migrations.scripts import backfill_barrier_changed_since_published
from api.barriers.models import Barrier, PublicBarrier
from api.barriers.signals.handlers import barrier_changed_after_published
from api.metadata.constants import PublicBarrierStatus, BarrierStatus
from api.metadata.models import Category
from tests.barriers.factories import BarrierFactory
from tests.barriers.test_public_barriers import PublicBarrierBaseTestCase


class PublicBarrierBaseTestCaseWorkingSignal(PublicBarrierBaseTestCase):
    def test_backfill_public_barrier_signal_works(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False

        signals.pre_save.connect(barrier_changed_after_published, sender=Barrier)

        barrier.title = "Updated"
        barrier.save()
        # Triggers barrier_changed_after_published signal

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True


class PublicBarrierBaseTestCase(PublicBarrierBaseTestCase):
    def test_backfill_public_barrier_title(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.title = "Updated"
        barrier.save()

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True

    def test_backfill_public_barrier_status(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False
        assert barrier.status == 1

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.status = BarrierStatus.OPEN_IN_PROGRESS
        barrier.save()

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is False
        assert barrier.status == 2

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True

    def test_backfill_public_barrier_country(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False
        assert barrier.country == "985f66a0-5d95-e211-a939-e4115bead28a"

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.country = "115f66a0-5d95-e211-a939-e4115bead222"
        barrier.save()

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True

    def test_backfill_public_barrier_summary(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.summary = "Updated"
        barrier.save()

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True

    def test_backfill_public_barrier_categories(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False

        assert barrier.categories.count() == 0

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.categories.add(Category.objects.first())
        barrier.save()

        assert barrier.categories.count() == 1

        # call_command("backfill_public_barrier_changed_since_published")

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True

    def test_backfill_public_barrier_sectors(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_published is False
        assert len(barrier.sectors) == 1

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.sectors = []
        barrier.save()

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True

    def test_backfill_public_barrier_categories_not_published_doesnt_set(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)

        assert public_barrier.changed_since_published is False

        assert barrier.categories.count() == 0

        signals.pre_save.disconnect(barrier_changed_after_published, sender=Barrier)

        barrier.categories.add(Category.objects.first())
        barrier.save()

        assert barrier.categories.count() == 1

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is False

        # Now publish
        public_barrier.publish()
        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        barrier.categories.remove(Category.objects.first())
        barrier.save()

        backfill_barrier_changed_since_published.run(
            historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
            public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
        )

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_published is True
