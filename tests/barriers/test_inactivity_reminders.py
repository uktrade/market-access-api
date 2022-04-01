from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.db.models import Q
from django.test import TestCase
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.models import Barrier
from api.barriers.tasks import send_barrier_inactivity_reminders
from api.core.test_utils import create_test_user
from tests.barriers.factories import BarrierFactory
from tests.collaboration.factories import TeamMemberFactory


class TestBarrierInactivityReminders(TestCase):
    def test_inactive_barrier_reminder_email(self):
        test_user = create_test_user()

        inactivity_theshold_date = datetime.now() - timedelta(
            days=settings.BARRIER_INACTIVITY_THESHOLD_DAYS
        )
        repeat_reminder_theshold_date = datetime.now() - timedelta(
            days=settings.BARRIER_REPEAT_REMINDER_THESHOLD_DAYS
        )

        BarrierFactory.create_batch(size=10)
        for barrier in Barrier.objects.all():
            TeamMemberFactory(
                barrier=barrier, user=test_user, role="Owner", default=True
            )
        # modified_on can't be updated directly, so we need to update the barrier queryset
        Barrier.objects.all().update(
            modified_on=inactivity_theshold_date - timedelta(days=1)
        )

        assert (
            Barrier.objects.filter(modified_on__lt=inactivity_theshold_date)
            .filter(
                Q(activity_reminder_sent__isnull=True)
                | Q(activity_reminder_sent__lt=repeat_reminder_theshold_date)
            )
            .count()
            == 10
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

    def test_individual_notification(self):
        test_user = create_test_user()
        inactivity_theshold_date = datetime.now() - timedelta(
            days=settings.BARRIER_INACTIVITY_THESHOLD_DAYS
        )
        repeat_reminder_theshold_date = datetime.now() - timedelta(
            days=settings.BARRIER_REPEAT_REMINDER_THESHOLD_DAYS
        )
        #  test individual call params
        test_barrier = BarrierFactory()
        TeamMemberFactory(
            barrier=test_barrier, user=test_user, role="Owner", default=True
        )
        Barrier.objects.filter(id=test_barrier.id).update(
            modified_on=inactivity_theshold_date - timedelta(days=1),
            activity_reminder_sent=None,
        )

        assert (
            test_barrier.id
            == Barrier.objects.filter(modified_on__lt=inactivity_theshold_date)
            .filter(
                Q(activity_reminder_sent__isnull=True)
                | Q(activity_reminder_sent__lt=repeat_reminder_theshold_date)
            )
            .first()
            .id
        )

        assert (
            Barrier.objects.filter(modified_on__lt=inactivity_theshold_date)
            .filter(
                Q(activity_reminder_sent__isnull=True)
                | Q(activity_reminder_sent__lt=repeat_reminder_theshold_date)
            )
            .count()
            == 1
        )

        with patch.object(NotificationsAPIClient, "send_email_notification") as mock:
            owner = test_barrier.barrier_team.get(role="Owner").user

            assert owner.email == test_user.email

            send_barrier_inactivity_reminders()

            email_personalisation = {
                "barrier_title": test_barrier.title,
                "barrier_url": f"{settings.DMAS_BASE_URL}/barriers/{test_barrier.id}/",
                "full_name": f"{owner.first_name} {owner.last_name}",
                "barrier_created_date": test_barrier.created_on.strftime("%d %B %Y"),
            }

            assert mock.call_count == 1
            mock.assert_called_once_with(
                email_address=owner.email,
                template_id=settings.BARRIER_INACTIVITY_REMINDER_NOTIFICATION_ID,
                personalisation=email_personalisation,
            )
