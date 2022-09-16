from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.models import Barrier
from api.barriers.tasks import (
    auto_update_inactive_barrier_status,
    send_auto_update_inactive_barrier_notification,
    send_barrier_inactivity_reminders,
)
from api.core.test_utils import create_test_user
from tests.barriers.factories import BarrierFactory
from tests.collaboration.factories import TeamMemberFactory
from tests.user.factories import UserFactoryMixin

User = get_user_model()


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


class TestAutoBarrierStatusUpdates(TestCase, UserFactoryMixin):
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

    def test_auto_status_change_notifications_multiple_regions(self):
        america_lead = self.create_standard_user(role="Regional Lead - North America")
        europe_lead = self.create_standard_user(role="Regional Lead - Europe")
        china_lead = self.create_standard_user(role="Regional Lead - China/Hong Kong")

        america_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada
        europe_barrier = BarrierFactory(
            country="84756b9a-5d95-e211-a939-e4115bead28a"
        )  # Italy
        china_barrier = BarrierFactory(
            country="63af72a6-5d95-e211-a939-e4115bead28a"
        )  # China

        test_barrier_list = [
            america_barrier,
            europe_barrier,
            china_barrier,
        ]

        for barrier in test_barrier_list:
            Barrier.objects.filter(id=barrier.id).update(
                modified_on=self.archival_threshold_date - timedelta(days=1), status=5
            )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if america_lead.first_name and america_lead.last_name in email_recipient:
                assert str(america_barrier) in archive_email_markup

            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(europe_barrier) in archive_email_markup

            if china_lead.first_name and china_lead.last_name in email_recipient:
                assert str(china_barrier) in archive_email_markup

            assert "1 barrier will be archived" in archive_email_markup
            assert (
                "No barriers will be made dormant in your region this month"
                in dormant_email_markup
            )

    def test_auto_status_change_notifications_america(self):
        america_lead = self.create_standard_user(role="Regional Lead - North America")
        america_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada
        Barrier.objects.filter(id=america_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if america_lead.first_name and america_lead.last_name in email_recipient:
                assert str(america_barrier) in archive_email_markup
                assert "Canada" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_europe(self):
        europe_lead = self.create_standard_user(role="Regional Lead - Europe")
        europe_barrier = BarrierFactory(
            country="84756b9a-5d95-e211-a939-e4115bead28a"
        )  # Italy
        Barrier.objects.filter(id=europe_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(europe_barrier) in archive_email_markup
                assert "Italy" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_china(self):
        china_lead = self.create_standard_user(role="Regional Lead - China/Hong Kong")
        china_barrier = BarrierFactory(
            country="63af72a6-5d95-e211-a939-e4115bead28a"
        )  # China
        Barrier.objects.filter(id=china_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if china_lead.first_name and china_lead.last_name in email_recipient:
                assert str(china_barrier) in archive_email_markup
                assert "China" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_latac(self):
        latac_lead = self.create_standard_user(role="Regional Lead - LATAC")
        latac_barrier = BarrierFactory(
            country="0e50bdb8-5d95-e211-a939-e4115bead28a"
        )  # Mexico
        Barrier.objects.filter(id=latac_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if latac_lead.first_name and latac_lead.last_name in email_recipient:
                assert str(latac_barrier) in archive_email_markup
                assert "Mexico" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_apac(self):
        apac_lead = self.create_standard_user(role="Regional Lead - APAC")
        apac_barrier = BarrierFactory(
            country="85756b9a-5d95-e211-a939-e4115bead28a"
        )  # Japan
        Barrier.objects.filter(id=apac_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if apac_lead.first_name and apac_lead.last_name in email_recipient:
                assert str(apac_barrier) in archive_email_markup
                assert "Japan" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_south_asia(self):
        south_asia_lead = self.create_standard_user(role="Regional Lead - South Asia")
        south_asia_barrier = BarrierFactory(
            country="6f6a9ab2-5d95-e211-a939-e4115bead28a"
        )  # India
        Barrier.objects.filter(id=south_asia_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if (
                south_asia_lead.first_name
                and south_asia_lead.last_name in email_recipient
            ):
                assert str(south_asia_barrier) in archive_email_markup
                assert "India" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_eecan(self):
        eecan_lead = self.create_standard_user(role="Regional Lead - EECAN")
        eecan_barrier = BarrierFactory(
            country="b36ee1ca-5d95-e211-a939-e4115bead28a"
        )  # Ukraine
        Barrier.objects.filter(id=eecan_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if eecan_lead.first_name and eecan_lead.last_name in email_recipient:
                assert str(eecan_barrier) in archive_email_markup
                assert "Ukraine" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_meap(self):
        meap_lead = self.create_standard_user(role="Regional Lead - MEAP")
        meap_barrier = BarrierFactory(
            country="87756b9a-5d95-e211-a939-e4115bead28a"
        )  # Afghanistan
        Barrier.objects.filter(id=meap_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if meap_lead.first_name and meap_lead.last_name in email_recipient:
                assert str(meap_barrier) in archive_email_markup
                assert "Afghanistan" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_africa(self):
        africa_lead = self.create_standard_user(role="Regional Lead - Africa")
        africa_barrier = BarrierFactory(
            country="4561b8be-5d95-e211-a939-e4115bead28a"
        )  # Nigeria
        Barrier.objects.filter(id=africa_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if africa_lead.first_name and africa_lead.last_name in email_recipient:
                assert str(africa_barrier) in archive_email_markup
                assert "Nigeria" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_wider_europe(self):
        wider_europe_lead = self.create_standard_user(
            role="Regional Lead - Wider Europe"
        )

        norway_barrier = BarrierFactory(country="4961b8be-5d95-e211-a939-e4115bead28a")
        switzerland_barrier = BarrierFactory(
            country="310be5c4-5d95-e211-a939-e4115bead28a"
        )
        iceland_barrier = BarrierFactory(country="6e6a9ab2-5d95-e211-a939-e4115bead28a")
        liechtenstein_barrier = BarrierFactory(
            country="856a9ab2-5d95-e211-a939-e4115bead28a"
        )
        israel_barrier = BarrierFactory(country="746a9ab2-5d95-e211-a939-e4115bead28a")
        albania_barrier = BarrierFactory(country="945f66a0-5d95-e211-a939-e4115bead28a")
        montenegro_barrier = BarrierFactory(
            country="7f756b9a-5d95-e211-a939-e4115bead28a"
        )
        north_macedonia_barrier = BarrierFactory(
            country="896a9ab2-5d95-e211-a939-e4115bead28a"
        )
        serbia_barrier = BarrierFactory(country="1c0be5c4-5d95-e211-a939-e4115bead28a")
        bosnia_herzegovina_barrier = BarrierFactory(
            country="ad5f66a0-5d95-e211-a939-e4115bead28a"
        )
        kosovo_barrier = BarrierFactory(country="7a756b9a-5d95-e211-a939-e4115bead28a")

        test_barrier_list = [
            norway_barrier,
            switzerland_barrier,
            iceland_barrier,
            liechtenstein_barrier,
            israel_barrier,
            albania_barrier,
            montenegro_barrier,
            north_macedonia_barrier,
            serbia_barrier,
            bosnia_herzegovina_barrier,
            kosovo_barrier,
        ]

        for barrier in test_barrier_list:
            Barrier.objects.filter(id=barrier.id).update(
                modified_on=self.archival_threshold_date - timedelta(days=1), status=5
            )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if (
                wider_europe_lead.first_name
                and wider_europe_lead.last_name in email_recipient
            ):
                for barrier in test_barrier_list:
                    assert str(barrier) in archive_email_markup
                assert "11 barriers will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_eu_bloc(self):
        europe_lead = self.create_standard_user(role="Regional Lead - Europe")
        europe_barrier = BarrierFactory(trading_bloc="TB00016", country=None)  # The EU
        Barrier.objects.filter(id=europe_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(europe_barrier) in archive_email_markup
                assert "Trading Bloc" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_gcc_bloc(self):
        europe_lead = self.create_standard_user(role="Regional Lead - MEAP")
        europe_barrier = BarrierFactory(trading_bloc="TB00017", country=None)  # The GCC
        Barrier.objects.filter(id=europe_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(europe_barrier) in archive_email_markup
                assert "Trading Bloc" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_eaeu_bloc(self):
        europe_lead = self.create_standard_user(role="Regional Lead - EECAN")
        europe_barrier = BarrierFactory(
            trading_bloc="TB00013", country=None
        )  # The EAEU
        Barrier.objects.filter(id=europe_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(europe_barrier) in archive_email_markup
                assert "Trading Bloc" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_mercosur_bloc(self):
        europe_lead = self.create_standard_user(role="Regional Lead - LATAC")
        europe_barrier = BarrierFactory(
            trading_bloc="TB00026", country=None
        )  # Mercosur
        Barrier.objects.filter(id=europe_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )
        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(europe_barrier) in archive_email_markup
                assert "Trading Bloc" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_uk(self):
        europe_lead = self.create_standard_user(role="Regional Lead - Europe")
        uk_barrier = BarrierFactory(country="80756b9a-5d95-e211-a939-e4115bead28a")

        Barrier.objects.filter(id=uk_barrier.id).update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if europe_lead.first_name and europe_lead.last_name in email_recipient:
                assert str(uk_barrier) in archive_email_markup
                assert "United Kingdom" in archive_email_markup
                assert "1 barrier will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_multiple_barriers(self):
        america_lead = self.create_standard_user(role="Regional Lead - North America")
        first_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada
        second_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada
        third_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada

        test_barrier_list = [
            first_barrier,
            second_barrier,
            third_barrier,
        ]

        for barrier in test_barrier_list:
            Barrier.objects.filter(id=barrier.id).update(
                modified_on=self.archival_threshold_date - timedelta(days=1), status=5
            )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if america_lead.first_name and america_lead.last_name in email_recipient:
                assert str(first_barrier) in archive_email_markup
                assert str(second_barrier) in archive_email_markup
                assert str(third_barrier) in archive_email_markup
                assert "3 barriers will be archived" in archive_email_markup
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_no_barriers(self):
        america_lead = self.create_standard_user(role="Regional Lead - North America")
        america_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if america_lead.first_name and america_lead.last_name in email_recipient:
                assert str(america_barrier) not in archive_email_markup
                assert str(america_barrier) not in dormant_email_markup
                assert (
                    "No barriers will be archived in your region this month"
                    in archive_email_markup
                )
                assert (
                    "No barriers will be made dormant in your region this month"
                    in dormant_email_markup
                )

    def test_auto_status_change_notifications_dormant_barriers(self):
        america_lead = self.create_standard_user(role="Regional Lead - North America")
        america_barrier = BarrierFactory(
            country="5daf72a6-5d95-e211-a939-e4115bead28a"
        )  # Canada

        Barrier.objects.filter(id=america_barrier.id).update(
            modified_on=self.dormancy_threshold_date - timedelta(days=1), status=2
        )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            email_recipient = call[1]["personalisation"]["full_name"]
            dormant_email_markup = call[1]["personalisation"]["barriers_to_be_dormant"]
            archive_email_markup = call[1]["personalisation"]["barriers_to_be_archived"]
            if america_lead.first_name and america_lead.last_name in email_recipient:
                assert str(america_barrier) in dormant_email_markup
                assert "Canada" in dormant_email_markup
                assert (
                    "No barriers will be archived in your region this month"
                    in archive_email_markup
                )
                assert "1 barrier will be made dormant" in dormant_email_markup

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

        # Barrier has passed the 18 month mark for auto dormancy
        with freeze_time("2021-07-01"):
            auto_update_inactive_barrier_status()
            time_frozen_barrier.refresh_from_db()
            assert time_frozen_barrier.status == 5

        # Barrier has passed the (further) 18 month mark for auto archival
        with freeze_time("2023-01-02"):
            auto_update_inactive_barrier_status()
            time_frozen_barrier.refresh_from_db()
            assert time_frozen_barrier.status == 6

    def test_auto_status_change_twenty_limit(self):
        europe_lead = self.create_standard_user(role="Regional Lead - Europe")
        test_user = create_test_user()

        # # Make sure we start with no unarchived barriers
        for barrier in Barrier.objects.all():
            barrier.archive(test_user, "Don't want this")
        # Create 25 barriers in the DB
        for i in range(0, 25):
            BarrierFactory(
                title=f"barry_the_barrier {i}",
                country="80756b9a-5d95-e211-a939-e4115bead28a",
            )

        # Update all barriers to be past threshold
        Barrier.objects.all().update(
            modified_on=self.archival_threshold_date - timedelta(days=1), status=5
        )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            send_auto_update_inactive_barrier_notification()

        for call in mock.call_args_list:
            barrier_count = str(call).count("barry_the_barrier")
            assert barrier_count == 20
