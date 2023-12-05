import logging

from api.history.factqories.action_plans import ActionPlanTaskHistoryFactory
from django.test import TestCase
from freezegun import freeze_time

from api.action_plans.models import ActionPlan
from api.assessment.models import EconomicAssessment
from api.barriers.helpers import get_or_create_public_barrier
from api.barriers.models import Barrier, BarrierProgressUpdate
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin
from api.core.utils import cleansed_username
from api.history.factories import (
    BarrierHistoryFactory,
    DeliveryConfidenceHistoryFactory,
    EconomicAssessmentHistoryFactory,
    NoteHistoryFactory,
    PublicBarrierHistoryFactory,
    PublicBarrierNoteHistoryFactory,
    TeamMemberHistoryFactory,
)
from api.history.items.action_plans import get_default_user
from api.history.models import CachedHistoryItem
from api.interactions.models import Interaction, PublicBarrierNote
from api.metadata.constants import PublicBarrierStatus
from tests.action_plans.factories import (
    ActionPlanMilestoneFactory,
    ActionPlanTaskFactory,
)
from tests.assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
    ResolvabilityAssessmentFactory,
    StrategicAssessmentFactory,
)
from tests.interactions.factories import InteractionFactory

logger = logging.getLogger(__name__)


class TestBarrierHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "categories", "users"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()

    def test_archived_history(self):
        self.barrier.archive(
            user=self.user, reason="DUPLICATE", explanation="It was a duplicate"
        )

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "archived"
        assert data["old_value"] == {
            "archived": False,
            "unarchived_reason": "",
        }
        assert data["new_value"] == {
            "archived": True,
            "archived_reason": "DUPLICATE",
            "archived_explanation": "It was a duplicate",
        }

    def test_priority_history(self):
        self.barrier.priority_id = 2
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "priority"
        assert data["old_value"] == {
            "priority": "UNKNOWN",
            "priority_summary": "",
        }
        assert data["new_value"] == {
            "priority": "HIGH",
            "priority_summary": "",
        }


class TestPublicBarrierHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "categories", "users"]

    @freeze_time("2020-03-02")
    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()
        self.public_barrier, _created = get_or_create_public_barrier(self.barrier)

    def test_public_view_status_history(self):
        self.barrier.public_eligibility = True
        self.barrier.public_eligibility_summary = "Allowed summary"
        self.barrier.save()
        self.public_barrier.public_view_status = PublicBarrierStatus.ELIGIBLE
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "public_view_status"
        assert data["old_value"] == {
            "public_view_status": {
                "id": PublicBarrierStatus.UNKNOWN,
                "name": PublicBarrierStatus.choices[PublicBarrierStatus.UNKNOWN],
            },
            "public_eligibility": None,
            "public_eligibility_summary": "",
        }
        assert data["new_value"] == {
            "public_view_status": {
                "id": PublicBarrierStatus.ELIGIBLE,
                "name": PublicBarrierStatus.choices[PublicBarrierStatus.ELIGIBLE],
            },
            "public_eligibility": True,
            "public_eligibility_summary": "Allowed summary",
        }

    def test_summary_history(self):
        self.public_barrier.summary = "New summary"
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "summary"
        assert data["old_value"] == ""
        assert data["new_value"] == "New summary"

    def test_note_text_history(self):
        note = PublicBarrierNote.objects.create(
            public_barrier=self.public_barrier,
            text="Original note",
            created_by=self.mock_user,
        )
        note.text = "Edited note"
        note.save()

        items = PublicBarrierNoteHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier_note"
        assert data["field"] == "text"
        assert data["old_value"] == "Original note"
        assert data["new_value"] == "Edited note"

    def test_note_archived_history(self):
        note = PublicBarrierNote.objects.create(
            public_barrier=self.public_barrier,
            text="Original note",
            created_by=self.mock_user,
        )
        note.archived = True
        note.save()

        items = PublicBarrierNoteHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier_note"
        assert data["field"] == "archived"
        assert data["old_value"] == {
            "archived": False,
            "text": "Original note",
        }
        assert data["new_value"] == {
            "archived": True,
            "text": "Original note",
        }


class TestEconomicAssessmentHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "documents", "users"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.assessment = EconomicAssessment.objects.create(
            barrier=self.barrier,
            rating="LOW",
            explanation="Some explanation",
            value_to_economy=10000,
            import_market_size=20000,
            export_value=40000,
        )

    def test_explanation_history(self):
        self.assessment.explanation = "New explanation"
        self.assessment.save()

        items = EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "economic_assessment"
        assert data["field"] == "explanation"
        assert data["old_value"] == "Some explanation"
        assert data["new_value"] == "New explanation"

    def test_rating_history(self):
        self.assessment.rating = "HIGH"
        self.assessment.save()

        items = EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "economic_assessment"
        assert data["field"] == "rating"
        assert data["old_value"]["name"] == "Low"
        assert data["new_value"]["name"] == "High"

    def test_documents_history(self):
        self.assessment.documents.add("fdb0624e-a549-4f70-b9a2-68896e4d1141")

        items = EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )

        data = items[-1].data

        assert data["model"] == "economic_assessment"
        assert data["field"] == "documents"
        assert data["old_value"] == []
        assert data["new_value"] == [
            {
                "id": "fdb0624e-a549-4f70-b9a2-68896e4d1141",
                "name": "dog.jpg",
            }
        ]

    def test_export_value_history(self):
        self.assessment.export_value = 2222
        self.assessment.save()

        items = EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "economic_assessment"
        assert data["field"] == "export_value"
        assert data["old_value"] == 40000
        assert data["new_value"] == 2222

    def test_import_market_size_history(self):
        self.assessment.import_market_size = 3333
        self.assessment.save()

        items = EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "economic_assessment"
        assert data["field"] == "import_market_size"
        assert data["old_value"] == 20000
        assert data["new_value"] == 3333

    def test_value_to_economy_history(self):
        self.assessment.value_to_economy = 4444
        self.assessment.save()

        items = EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "economic_assessment"
        assert data["field"] == "value_to_economy"
        assert data["old_value"] == 10000
        assert data["new_value"] == 4444


class TestNoteHistory(APITestMixin, TestCase):
    fixtures = ["documents", "users", "barriers"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()
        self.note = Interaction.objects.create(
            barrier=self.barrier,
            kind="COMMENT",
            text="Original note",
            created_by=self.mock_user,
        )

    def test_documents_history(self):
        self.note.documents.add("eda7ee4e-4786-4507-a0ed-05a10169764b")

        items = NoteHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "note"
        assert data["field"] == "documents"
        assert data["old_value"] == []
        assert data["new_value"] == [
            {
                "id": "eda7ee4e-4786-4507-a0ed-05a10169764b",
                "name": "cat.jpg",
            }
        ]

    def test_text_history(self):
        self.note.text = "Edited note"
        self.note.save()

        items = NoteHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "note"
        assert data["field"] == "text"
        assert data["old_value"] == "Original note"
        assert data["new_value"] == "Edited note"


class TestTeamMemberHistory(APITestMixin, TestCase):
    fixtures = ["users", "barriers"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()

    def test_team_member_history(self):
        TeamMember.objects.create(
            barrier=self.barrier, user=self.user, role="Contributor"
        )

        items = TeamMemberHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "team_member"
        assert data["field"] == "user"
        assert data["old_value"] is None
        assert data["new_value"] == {
            "user": {"id": 5, "name": "Testo Useri"},
            "role": "Contributor",
        }


class TestProgressUpdateHistory(APITestMixin, TestCase):
    fixtures = ["users", "barriers"]
    # make django-test path=barriers/test_history.py::TestProgressUpdateHistory

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()

    def test_history_created_progress_updates(self):
        # Ensure history returns sequence of "created" progress updates

        BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status="ON_TRACK",
            update="Nothing Specific",
            next_steps="Finish writing these tests.",
        )

        BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status="DELAYED",
            update="Nothing Specific",
            next_steps="Get coffee.",
        )

        items = DeliveryConfidenceHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )

        # Expect (from earliest to latest):
        # ON_TRACK set, no previous
        # ON_TRACK changes to DELAYED
        assert items[0].data["old_value"] == {"status": "", "summary": ""}
        assert items[0].data["new_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[1].data["old_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[1].data["new_value"] == {
            "status": "Delayed",
            "summary": "Nothing Specific",
        }

    def test_history_edited_progress_updates(self):
        # Ensure history returns a "created" progress update and a subsequent edit
        self.progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status="ON_TRACK",
            update="Nothing Specific",
            next_steps="Finish writing these tests.",
        )

        self.progress_update.status = "DELAYED"
        self.progress_update.save()

        items = DeliveryConfidenceHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )

        # Expect (from earliest to latest):
        # ON_TRACK set, no previous
        # ON_TRACK changes to DELAYED
        assert items[0].data["old_value"] == {"status": "", "summary": ""}
        assert items[0].data["new_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[1].data["old_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[1].data["new_value"] == {
            "status": "Delayed",
            "summary": "Nothing Specific",
        }

    def test_history_non_linear_updates(self):
        # Ensure history returns a sequence of "created" progress updates, and an edit to
        # a progress update created early in the sequence
        self.progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status="ON_TRACK",
            update="Nothing Specific",
            next_steps="Finish writing these tests.",
        )

        BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status="DELAYED",
            update="Nothing Specific",
            next_steps="Get coffee.",
        )

        self.progress_update.status = "RISK_OF_DELAY"
        self.progress_update.save()

        items = DeliveryConfidenceHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )

        # Expect (from earliest to latest):
        # ON_TRACK set, no previous
        # ON_TRACK changes to DELAYED
        # ON_TRACK changes to RISK_OF_DELAY
        assert items[0].data["old_value"] == {"status": "", "summary": ""}
        assert items[0].data["new_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[1].data["old_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[1].data["new_value"] == {
            "status": "Delayed",
            "summary": "Nothing Specific",
        }
        assert items[2].data["old_value"] == {
            "status": "On track",
            "summary": "Nothing Specific",
        }
        assert items[2].data["new_value"] == {
            "status": "Risk of delay",
            "summary": "Nothing Specific",
        }


class TestCachedHistoryItems(APITestMixin, TestCase):
    fixtures = ["categories", "documents", "users", "barriers"]

    @freeze_time("2020-03-02")
    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()

        self.assessment = EconomicAssessmentFactory(
            barrier=self.barrier, rating="LOW", created_by=self.mock_user
        )
        self.note = InteractionFactory(
            barrier=self.barrier, text="Original note", created_by=self.mock_user
        )
        self.public_barrier, _created = get_or_create_public_barrier(self.barrier)

    @freeze_time("2020-04-01")
    def test_cached_history_items(self):
        CachedHistoryItem.objects.all().delete()

        # Barrier changes
        self.barrier.categories.add("109", "115")
        self.barrier.commercial_value = 55555
        self.barrier.commercial_value_explanation = "Explanation"
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.summary = "New summary"
        self.barrier.country = "81756b9a-5d95-e211-a939-e4115bead28a"  # USA
        self.barrier.admin_areas = [
            "a88512e0-62d4-4808-95dc-d3beab05d0e9"
        ]  # California
        self.barrier.priority_id = 2
        self.barrier.product = "New product"
        self.barrier.status = 5
        self.barrier.status_summary = "Summary"
        self.barrier.sub_status = "UK_GOVT"
        self.barrier.term = 1
        self.barrier.public_eligibility_summary = "New summary"
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.source = "COMPANY"
        self.barrier.title = "New title"
        self.barrier.save()

        self.barrier.archive(
            user=self.user, reason="DUPLICATE", explanation="It was a duplicate"
        )

        # Note changes
        self.note.documents.add("eda7ee4e-4786-4507-a0ed-05a10169764b")
        self.note.text = "Edited note"
        self.note.save()

        # Team Member changes
        TeamMember.objects.create(
            barrier=self.barrier, user=self.user, role="Contributor"
        )

        with patch.object(
            NotificationsAPIClient, "send_email_notification", return_value=None
        ) as mock:
            # Assessment changes
            economic_assessment = EconomicAssessmentFactory(
                barrier=self.barrier,
                rating="LOW",
            )
            EconomicImpactAssessmentFactory(
                economic_assessment=economic_assessment,
                barrier=economic_assessment.barrier,
                impact=4,
            )
            ResolvabilityAssessmentFactory(
                barrier=self.barrier,
                time_to_resolve=4,
                effort_to_resolve=1,
            )
            StrategicAssessmentFactory(
                barrier=self.barrier,
                scale=3,
                uk_grants="Testing",
            )

        # Public barrier changes
        self.public_barrier.categories.add("109", "115")
        self.public_barrier.country = "570507cc-1592-4a99-afca-915d13a437d0"
        self.public_barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.public_barrier.status = 4
        self.public_barrier.public_view_status = PublicBarrierStatus.ELIGIBLE
        self.public_barrier.summary = "New summary"
        self.public_barrier.title = "New title"
        self.public_barrier.save()

        items = CachedHistoryItem.objects.filter(barrier=self.barrier).values(
            "model", "field"
        )
        cached_changes = [(item["model"], item["field"]) for item in items]

        assert ("barrier", "archived") in cached_changes
        assert ("barrier", "categories") in cached_changes
        assert ("barrier", "companies") in cached_changes
        assert ("barrier", "location") in cached_changes
        assert ("barrier", "priority") in cached_changes
        assert ("barrier", "product") in cached_changes
        assert ("barrier", "term") in cached_changes
        assert ("barrier", "sectors") in cached_changes
        assert ("barrier", "source") in cached_changes
        assert ("barrier", "status") in cached_changes
        assert ("barrier", "summary") in cached_changes
        assert ("barrier", "title") in cached_changes
        assert ("economic_assessment", "rating") in cached_changes
        assert ("economic_assessment", "explanation") in cached_changes
        assert ("economic_impact_assessment", "impact") in cached_changes
        assert ("economic_impact_assessment", "explanation") in cached_changes
        assert ("resolvability_assessment", "time_to_resolve") in cached_changes
        assert ("resolvability_assessment", "effort_to_resolve") in cached_changes
        assert ("strategic_assessment", "scale") in cached_changes
        assert ("strategic_assessment", "uk_grants") in cached_changes
        assert ("note", "documents") in cached_changes
        assert ("note", "text") in cached_changes
        assert ("team_member", "user") in cached_changes
        assert ("public_barrier", "categories") in cached_changes
        assert ("public_barrier", "location") in cached_changes
        assert ("public_barrier", "public_view_status") in cached_changes
        assert ("public_barrier", "sectors") in cached_changes
        assert ("public_barrier", "status") in cached_changes
        assert ("public_barrier", "summary") in cached_changes
        assert ("public_barrier", "title") in cached_changes


class TestActionPlanHistory(APITestMixin, TestCase):
    fixtures = ["users", "barriers"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")

    def test_action_plan_no_user_history(self):
        action_plan = ActionPlan.objects.get(barrier=self.barrier)
        milestone = ActionPlanMilestoneFactory(action_plan=action_plan)
        action_plan = ActionPlanTaskFactory(milestone=milestone, assigned_to=None)

        action_plan.assigned_to = self.mock_user
        action_plan.save()

        items = ActionPlanTaskHistoryFactory.get_history_items(
            barrier_id=self.barrier.id,
        )
        data = items[-1].data
        default_user = get_default_user()

        # asserting that when the old value of assigned_to is None, the default user is returned
        assert data["old_value"] == cleansed_username(default_user)
