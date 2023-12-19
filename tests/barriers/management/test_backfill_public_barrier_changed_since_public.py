from django.core.management import call_command

from api.metadata.constants import BarrierStatus, PublicBarrierStatus
from api.metadata.models import Category
from tests.barriers.factories import BarrierFactory
from tests.barriers.test_public_barriers import PublicBarrierBaseTestCase


class PublicBarrierBaseTestCase(PublicBarrierBaseTestCase):
    def test_backfill_public_barrier_title(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False

        barrier.title = "Updated"
        barrier.save()

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is True

    def test_backfill_public_barrier_status(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False
        assert barrier.status == 1

        barrier.status = BarrierStatus.OPEN_IN_PROGRESS
        barrier.save()

        assert barrier.status == 2

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is True

    def test_backfill_public_barrier_country(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False
        assert barrier.country == "985f66a0-5d95-e211-a939-e4115bead28a"

        barrier.country = "115f66a0-5d95-e211-a939-e4115bead222"
        barrier.save()

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is True

    def test_backfill_public_barrier_summary(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False

        barrier.summary = "Updated"
        barrier.save()

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is True

    def test_backfill_public_barrier_categories(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False

        assert barrier.categories.count() == 0

        barrier.categories.add(Category.objects.first())
        barrier.save()

        assert barrier.categories.count() == 1

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is True

    def test_backfill_public_barrier_sectors(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False
        assert len(barrier.sectors) == 1

        barrier.sectors = []
        barrier.save()

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is True

    def test_backfill_public_barrier_categories_not_published_doesnt_set(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)

        assert public_barrier.changed_since_public is False

        assert barrier.categories.count() == 0

        barrier.categories.add(Category.objects.first())
        barrier.save()

        assert barrier.categories.count() == 1

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is False

    def test_backfill_public_barrier_not_changed(self):
        barrier = BarrierFactory()
        public_barrier = self.get_public_barrier(barrier)
        public_barrier.publish()

        public_barrier.public_view_status = PublicBarrierStatus.PUBLISHED
        public_barrier.save()

        assert public_barrier.changed_since_public is False

        call_command("backfill_public_barrier_changed_since_public", dry_run=True)

        public_barrier = self.get_public_barrier(barrier)
        assert public_barrier.changed_since_public is False
