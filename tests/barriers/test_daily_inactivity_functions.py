from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.models import Barrier
from api.barriers.tasks import (
    auto_update_inactive_barrier_status,
    send_barrier_inactivity_reminders,
)
from api.core.test_utils import create_test_user
from tests.barriers.factories import BarrierFactory
from tests.collaboration.factories import TeamMemberFactory


class TestBarrierInactivityReminders(TestCase):
    def test_inactive_barrier_reminder_email(self):
        test_user = create_test_user()

        inactivity_threshold_date = timezone.now() - timedelta(
            days=settings.BARRIER_INACTIVITY_THRESHOLD_DAYS
        )
        BarrierFactory.create_batch(size=10)
        for barrier in Barrier.objects.all():
            TeamMemberFactory(
                barrier=barrier, user=test_user, role="Owner", default=True
            )
        # modified_on can't be updated directly, so we need to update the barrier queryset
        Barrier.objects.all().update(
            modified_on=inactivity_threshold_date - timedelta(days=1)
        )

        # create recent barries that should not be sent a reminder
        BarrierFactory.create_batch(size=15)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_barrier_inactivity_reminders()

            assert mock.call_count == 10
            assert (
                Barrier.objects.filter(activity_reminder_sent__isnull=False).count()
                == 10
            )
            mock.stop()

        #  when called a second time, no new reminders should be sent

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_barrier_inactivity_reminders()

            assert mock.call_count == 0
            assert (
                Barrier.objects.filter(activity_reminder_sent__isnull=False).count()
                == 10
            )
            mock.stop()

    def test_individual_barrier_reminder_email(self):
        test_user = create_test_user()
        inactivity_threshold_date = timezone.now() - timedelta(
            days=settings.BARRIER_INACTIVITY_THRESHOLD_DAYS
        )
        #  test individual call params
        test_barrier = BarrierFactory()
        TeamMemberFactory(
            barrier=test_barrier, user=test_user, role="Owner", default=True
        )
        Barrier.objects.filter(id=test_barrier.id).update(
            modified_on=inactivity_threshold_date - timedelta(days=1),
            activity_reminder_sent=None,
        )

        with patch.object(NotificationsAPIClient, "send_email_notification") as mock:

            send_barrier_inactivity_reminders()

            email_personalisation = {
                "barrier_title": test_barrier.title,
                "barrier_url": f"{settings.DMAS_BASE_URL}/barriers/{test_barrier.id}/",
                "full_name": f"{test_user.first_name} {test_user.last_name}",
                "barrier_created_date": test_barrier.created_on.strftime("%d %B %Y"),
            }

            assert mock.call_count == 1
            mock.assert_called_once_with(
                email_address=test_user.email,
                template_id=settings.BARRIER_INACTIVITY_REMINDER_NOTIFICATION_ID,
                personalisation=email_personalisation,
            )
            mock.stop()


class TestAutoBarrierStatusUpdates(TestCase):
    def setUp(self):
        super().setUp()
        self.dormancy_threshold_date = timezone.now() - timedelta(
            days=settings.BARRIER_INACTIVITY_DORMANT_THRESHOLD_DAYS
        )
        self.archival_threshold_date = timezone.now() - timedelta(
            days=settings.BARRIER_INACTIVITY_ARCHIVE_THRESHOLD_DAYS
        )
        self.test_barrier = BarrierFactory()

    def test_no_barriers_to_update(self):
        auto_update_inactive_barrier_status()
        # Barrier was created today, so is not eligible for dormancy/archival
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 1

    def test_barriers_to_make_dormant(self):
        Barrier.objects.filter(id=self.test_barrier.id).update(
            modified_on=self.dormancy_threshold_date - timedelta(days=1),
        )
        assert self.test_barrier.status == 1
        auto_update_inactive_barrier_status()
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 5

    def test_barriers_to_archive(self):
        Barrier.objects.filter(id=self.test_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 5
        auto_update_inactive_barrier_status()
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 6
        assert self.test_barrier.archived is True
        assert self.test_barrier.archived_reason == "Other"
        assert (
            self.test_barrier.archived_explanation
            == "Barrier has been inactive longer than the threshold for archival."
        )

    def test_barriers_in_all_states(self):
        BarrierFactory.create_batch(size=5, summary="dormant me")
        BarrierFactory.create_batch(size=5, summary="archive me")

        Barrier.objects.filter(summary="dormant me").update(
            modified_on=self.dormancy_threshold_date - timedelta(days=1),
        )
        Barrier.objects.filter(summary="archive me").update(
            modified_on=self.archival_threshold_date - timedelta(days=1),
            status=5,
        )
        auto_update_inactive_barrier_status()

        active_barriers = Barrier.objects.filter(status=1)
        dormant_barriers = Barrier.objects.filter(status=5)
        archived_barriers = Barrier.objects.filter(status=6)

        assert active_barriers.count() == 1
        assert dormant_barriers.count() == 5
        assert archived_barriers.count() == 5

    def test_barriers_resolved_in_full_not_made_dormant(self):
        Barrier.objects.filter(id=self.test_barrier.id).update(
            modified_on=self.dormancy_threshold_date - timedelta(days=1),
            status=4,
        )
        auto_update_inactive_barrier_status()
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 4

    def test_barriers_resolved_in_part_not_made_dormant(self):
        Barrier.objects.filter(id=self.test_barrier.id).update(
            modified_on=self.dormancy_threshold_date - timedelta(days=1),
            status=3,
        )
        auto_update_inactive_barrier_status()
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 3

    def test_barriers_archived_not_made_dormant(self):
        Barrier.objects.filter(id=self.test_barrier.id).update(
            modified_on=self.dormancy_threshold_date - timedelta(days=1),
            status=6,
        )
        auto_update_inactive_barrier_status()
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 6

    def test_barriers_non_dormant_not_archived(self):
        Barrier.objects.filter(id=self.test_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1),
        )
        self.test_barrier.refresh_from_db()
        assert self.test_barrier.status == 1
        auto_update_inactive_barrier_status()
        self.test_barrier.refresh_from_db()
        # Barrier which is past archive date but not dormant will
        # be made dormant.
        assert self.test_barrier.status == 5
        assert self.test_barrier.archived is False

    def test_barriers_inactivity_end_to_end(self):
        # Create a barrier, it won't trigger any status updates
        with freeze_time("2020-01-01"):
            time_frozen_barrier = BarrierFactory()
            auto_update_inactive_barrier_status()
            time_frozen_barrier.refresh_from_db()
            assert time_frozen_barrier.status == 1

        # Barrier has passed the 6 month mark for general inactivity reminder
        with freeze_time("2020-07-01"):
            send_barrier_inactivity_reminders()
            auto_update_inactive_barrier_status()
            time_frozen_barrier.refresh_from_db()
            assert time_frozen_barrier.status == 1

        # Barrier has passed the 12 month mark for auto dormancy
        with freeze_time("2021-02-01"):
            auto_update_inactive_barrier_status()
            time_frozen_barrier.refresh_from_db()
            assert time_frozen_barrier.status == 5

        # Barrier has passed the 18 month mark for auto archival
        with freeze_time("2022-02-01"):
            auto_update_inactive_barrier_status()
            time_frozen_barrier.refresh_from_db()
            assert time_frozen_barrier.status == 6
