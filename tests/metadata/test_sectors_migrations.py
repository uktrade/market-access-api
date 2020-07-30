import uuid

from tests.barriers.factories import BarrierFactory
from tests.barriers.test_report_progress import BarrierStatus
from tests.base import TestMigrations


class TestMassTransportMigration(TestMigrations):
    """
    This test case is inteded to test the logic in the migration itself rather than the mapping.
    Using a sector called Mass Transport as that sector has been split to 3 new ones.
    If the migration works with this then it will work with simpler cases too.
    """
    app = 'metadata'
    migrate_from = '0013_barriertag'
    migrate_to = '0014_sectors'

    def setUpBeforeMigration(self, apps):
        self.mass_transport_uuid_str = 'b5959812-6095-e211-a939-e4115bead28a'
        self.barrier = BarrierFactory(
            sectors=[self.mass_transport_uuid_str]
        )
        self.expected_sectors = [
            uuid.UUID('9738cecc-5f95-e211-a939-e4115bead28a'),  # Airports
            uuid.UUID('aa22c9d2-5f95-e211-a939-e4115bead28a'),  # Railways
            uuid.UUID('aa38cecc-5f95-e211-a939-e4115bead28a'),  # Maritime
        ]

        assert 1 == len(self.barrier.sectors)
        assert [self.mass_transport_uuid_str] == self.barrier.sectors
        assert 4 == self.barrier.history.count()

        # create a history items
        self.barrier.status = BarrierStatus.OPEN_IN_PROGRESS
        self.barrier.save()
        self.barrier.refresh_from_db()

        assert 5 == self.barrier.history.count()

    def test_sectors_migrated_in_barrier(self):
        self.barrier.refresh_from_db()
        assert set(self.expected_sectors) == set(self.barrier.sectors)

    def test_sectors_migration_removed_old_sector_id_in_history_items(self):
        history_items = self.barrier.history.filter(
            sectors__contains=[self.mass_transport_uuid_str]
        )
        assert 0 == history_items.count()

    def test_sectors_migration_does_not_create_a_new_history_item(self):
        assert 5 == self.barrier.history.count()

    def test_sectors_migration_adds_dest_sector_ids_to_history_items(self):
        for sector in self.expected_sectors:
            with self.subTest(sector=sector):
                history_items = self.barrier.history.filter(
                    sectors__contains=[sector]
                )
                assert 5 == history_items.count()
