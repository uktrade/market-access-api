import datetime
import logging
from unittest.mock import call, patch

from django.conf import settings
from django.test import TestCase
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.models import Barrier
from api.barriers.signals.handlers import (
    barrier_completion_top_priority_barrier_status_update,
    barrier_priority_approval_email_notification,
)
from api.core.test_utils import APITestMixin, create_test_user
from tests.barriers.factories import BarrierFactory
from tests.collaboration.factories import TeamMemberFactory

from ..assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
    ResolvabilityAssessmentFactory,
    StrategicAssessmentFactory,
)

logger = logging.getLogger(__name__)


class TestSignalFunctions(APITestMixin, TestCase):
    def test_barrier_priority_email_notification_accepted(self):
        barrier = BarrierFactory(top_priority_status="APPROVAL_PENDING")
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            barrier.top_priority_status = "APPROVED"
            barrier.save()

            barrier_priority_approval_email_notification(
                sender=Barrier, instance=barrier
            )

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.code),
                "barrier_url": f"https://dummy.market-access.net/barriers/{barrier.id}/",
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.BARRIER_PB100_ACCEPTED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_barrier_priority_email_notification_rejected(self):
        barrier = BarrierFactory(top_priority_status="APPROVAL_PENDING")
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            barrier.top_priority_status = "NONE"
            barrier.top_priority_rejection_summary = (
                "Because you didn't offer me coffee earlier. Rude."
            )
            barrier.save()

            barrier_priority_approval_email_notification(
                sender=Barrier, instance=barrier
            )

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.code),
                "barrier_url": f"https://dummy.market-access.net/barriers/{barrier.id}/",
                "decision_reason": barrier.top_priority_rejection_summary,
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.BARRIER_PB100_REJECTED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_barrier_priority_email_notification_skipped(self):
        barrier = BarrierFactory(top_priority_status="APPROVAL_PENDING")
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            barrier.source = "Ketchup"
            barrier.save()

            barrier_priority_approval_email_notification(
                sender=Barrier, instance=barrier
            )

            mock.assert_not_called()

            mock.stop()

    def test_resolving_barrier_resolves_top_priority(self):
        barrier = BarrierFactory(status=1, top_priority_status="APPROVED")
        barrier.status = 4
        barrier.save()

        barrier_completion_top_priority_barrier_status_update(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "RESOLVED"

    def test_reopening_resolved_top_priority_removes_resolved_tag(self):
        barrier = BarrierFactory(
            status=4, top_priority_status="APPROVED", status_date=datetime.date.today()
        )
        barrier.status = 1
        barrier.save()

        barrier_completion_top_priority_barrier_status_update(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "APPROVED"

    def test_resolving_top_priority_pending_barrier_retains_pending_tag(self):
        barrier = BarrierFactory(status=1, top_priority_status="APPROVAL_PENDING")
        barrier.status = 4
        barrier.save()

        barrier_completion_top_priority_barrier_status_update(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "APPROVAL_PENDING"

    def test_resolving_in_part_top_priority_barrier_retains_original_tag(self):
        barrier = BarrierFactory(status=1, top_priority_status="APPROVED")
        barrier.status = 3
        barrier.save()

        barrier_completion_top_priority_barrier_status_update(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "APPROVED"

    def test_new_valuation_commercial_value(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            barrier.commercial_value = 1000
            barrier.commercial_value_explanation = "Explaination"
            barrier.save()

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.id),
                "barrier_code": str(barrier.code),
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_new_valuation_economic_assessment(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            EconomicAssessmentFactory(
                barrier=barrier,
                rating="LOW",
            )

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.id),
                "barrier_code": str(barrier.code),
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_new_valuation_economic_impact_assessment(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            EconomicImpactAssessmentFactory(barrier=barrier, impact=4)

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.id),
                "barrier_code": str(barrier.code),
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_new_valuation_resolvability_assessment(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            ResolvabilityAssessmentFactory(barrier=barrier)

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.id),
                "barrier_code": str(barrier.code),
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_new_valuation_strategic_assessment(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            StrategicAssessmentFactory(barrier=barrier)

            expected_personalisation = {
                "first_name": test_user.first_name,
                "barrier_id": str(barrier.id),
                "barrier_code": str(barrier.code),
            }

            mock.assert_called_with(
                email_address=test_user.email,
                template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                personalisation=expected_personalisation,
            )

            mock.stop()

    def test_edit_assessment_no_notification(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            assessment = StrategicAssessmentFactory(barrier=barrier)
            assessment.additional_information = "Updated additional info"
            assessment.save()

            # Only called once - when the assessement is added
            assert mock.call_count == 1

            mock.stop()

    def test_edit_barrier_no_notification(self):
        barrier = Barrier()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            barrier.status = 3
            barrier.save()

            assert mock.call_count == 0

            mock.stop()

    def test_new_valuation_notification_mulitple_users(self):
        barrier = Barrier()
        test_owner = create_test_user()
        test_contributor = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_owner, role="Owner", default=True)
        TeamMemberFactory(
            barrier=barrier, user=test_contributor, role="Contributor", default=True
        )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:

            barrier.commercial_value = 1000
            barrier.commercial_value_explanation = "Explaination"
            barrier.save()

            assert mock.call_count == 2

            calls = [
                call(
                    email_address=test_owner.email,
                    personalisation={
                        "first_name": test_owner.first_name,
                        "barrier_id": str(barrier.id),
                        "barrier_code": str(barrier.code),
                    },
                    template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                ),
                call(
                    email_address=test_contributor.email,
                    personalisation={
                        "first_name": test_contributor.first_name,
                        "barrier_id": str(barrier.id),
                        "barrier_code": str(barrier.code),
                    },
                    template_id=settings.ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID,
                ),
            ]
            mock.assert_has_calls(calls, any_order=True)

            mock.stop()
