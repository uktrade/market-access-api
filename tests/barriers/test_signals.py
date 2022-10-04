import logging
from unittest.mock import call, patch

from django.conf import settings
from django.test import TestCase
from notifications_python_client.notifications import NotificationsAPIClient

from api.barriers.models import Barrier
from api.barriers.signals.handlers import (
    barrier_completion_percentage_changed,
    barrier_completion_top_priority_barrier_resolved,
    barrier_priority_approval_email_notification,
)
from api.core.test_utils import APITestMixin, create_test_user
from tests.barriers.factories import BarrierFactory, CommodityFactory
from tests.collaboration.factories import TeamMemberFactory
from tests.metadata.factories import CategoryFactory

from ..assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
    ResolvabilityAssessmentFactory,
    StrategicAssessmentFactory,
)

logger = logging.getLogger(__name__)


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

        barrier_completion_top_priority_barrier_resolved(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "RESOLVED"

    def test_resolving_top_priority_pending_barrier_retains_pending_tag(self):
        barrier = BarrierFactory(status=1, top_priority_status="APPROVAL_PENDING")
        barrier.status = 4
        barrier.save()

        barrier_completion_top_priority_barrier_resolved(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "APPROVAL_PENDING"

    def test_resolving_in_part_top_priority_barrier_retains_original_tag(self):
        barrier = BarrierFactory(status=1, top_priority_status="APPROVED")
        barrier.status = 3
        barrier.save()

        barrier_completion_top_priority_barrier_resolved(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "APPROVED"

    def test_reopening_resolved_top_priority_retains_resolved_tag(self):
        barrier = BarrierFactory(status=1, top_priority_status="RESOLVED")
        # Resolve the barrier
        barrier.status = 4
        barrier.save()
        # Reopen the barrier
        barrier.status = 1
        barrier.save()

        barrier_completion_top_priority_barrier_resolved(
            sender=Barrier, instance=barrier
        )

        barrier.refresh_from_db()

        assert barrier.top_priority_status == "RESOLVED"

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
                    template_id="",
                ),
                call(
                    email_address=test_contributor.email,
                    personalisation={
                        "first_name": test_contributor.first_name,
                        "barrier_id": str(barrier.id),
                        "barrier_code": str(barrier.code),
                    },
                    template_id="",
                ),
            ]
            mock.assert_has_calls(calls, any_order=True)

            mock.stop()
