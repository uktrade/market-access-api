import datetime
import logging

import freezegun
from django.test import TestCase

from api.action_plans.models import ActionPlan, ActionPlanTask
from api.assessment.models import EconomicAssessment
from api.barriers.helpers import get_or_create_public_barrier
from api.barriers.models import Barrier, BarrierProgressUpdate
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin
from api.history.factories import PublicBarrierHistoryFactory, TeamMemberHistoryFactory
from api.history.v2.enrichment import (
    enrich_committee_notified,
    enrich_committee_raised_in,
    enrich_priority_level,
    enrich_rating,
    enrich_sectors,
    enrich_status,
    enrich_wto_notified_status,
)
from api.metadata.constants import PRIORITY_LEVELS, PublicBarrierStatus
from api.wto.models import WTOProfile
from tests.action_plans.factories import (
    ActionPlanMilestoneFactory,
    ActionPlanTaskFactory,
)
from tests.barriers.factories import WTOCommitteeFactory, WTOProfileFactory
from tests.metadata.factories import OrganisationFactory

freezegun.configure(extend_ignore_list=["transformers"])

logger = logging.getLogger(__name__)


class TestBarrierHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "users", "policy_teams"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.draft = False
        self.barrier.save()

    def test_archived_history(self):
        self.barrier.archive(
            user=self.user, reason="DUPLICATE", explanation="It was a duplicate"
        )

        data = Barrier.get_history(barrier_id=self.barrier.pk)[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "archived"
        assert data["old_value"]["archived"] is False
        assert data["old_value"]["unarchived_reason"] == ""
        assert data["new_value"]["archived"] is True
        assert data["new_value"]["archived_reason"] == "DUPLICATE"
        assert data["new_value"]["archived_explanation"] == "It was a duplicate"

    def test_policy_teams_history(self):
        self.barrier.policy_teams.add("1", "2")

        data = Barrier.get_history(barrier_id=self.barrier.pk)[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "policy_teams"
        assert data["old_value"] == []
        assert set(data["new_value"]) == {1, 2}

    def test_organisations_history(self):
        org1 = OrganisationFactory()
        self.barrier.organisations.add(org1)
        self.barrier.save()

        data = Barrier.get_history(barrier_id=self.barrier.pk)[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "organisations"
        assert data["old_value"] == []
        assert set(data["new_value"]) == {org1.id}

    def test_companies_history(self):
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.save()

        data = Barrier.get_history(barrier_id=self.barrier.pk)[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "companies"
        assert data["old_value"] == []
        assert data["new_value"] == ["1", "2", "3"]

    def test_priority_history(self):
        self.barrier.priority_id = 2
        self.barrier.save()

        data = Barrier.get_history(barrier_id=self.barrier.pk)[-1]

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

    def test_priority_level_history(self):
        self.barrier.priority_level = PRIORITY_LEVELS.REGIONAL
        self.barrier.save()

        v2_history = Barrier.get_history(barrier_id=self.barrier.pk)
        enrich_priority_level(v2_history)
        data = v2_history[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "priority_level"
        assert data["old_value"] == ""
        assert data["new_value"] == "Regional Priority"

        self.barrier.priority_level = PRIORITY_LEVELS.COUNTRY
        self.barrier.save()

        v2_history = Barrier.get_history(barrier_id=self.barrier.pk)
        enrich_priority_level(v2_history)
        data = v2_history[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "priority_level"
        assert data["old_value"] == "Regional Priority"
        assert data["new_value"] == "Country Priority"

    def test_product_history(self):
        self.barrier.product = "New product"
        self.barrier.save()

        data = Barrier.get_history(barrier_id=self.barrier.pk)[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "product"
        assert data["old_value"] == "Some product"
        assert data["new_value"] == "New product"

    def test_status_history(self):
        self.barrier.status = 5
        self.barrier.status_summary = "Summary"
        self.barrier.sub_status = "UK_GOVT"
        self.barrier.save()

        v2_history = Barrier.get_history(barrier_id=self.barrier.pk)
        enrich_status(v2_history)
        data = v2_history[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "status"
        assert data["old_value"] == {
            "status": "1",
            "status_date": datetime.date(2019, 4, 9),
            "status_summary": "",
            "sub_status": "",
            "sub_status_other": "",
        }
        assert data["new_value"] == {
            "status": "5",
            "status_date": datetime.date(2019, 4, 9),
            "status_summary": "Summary",
            "sub_status": "UK_GOVT",
            "sub_status_other": "",
        }

    def test_sectors_history(self):
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.save()

        v2_history = Barrier.get_history(barrier_id=self.barrier.pk)
        enrich_sectors(v2_history)
        data = v2_history[-1]

        assert data["model"] == "barrier"
        assert data["field"] == "sectors"
        assert data["old_value"]["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert data["new_value"]["sectors"] == ["9538cecc-5f95-e211-a939-e4115bead28a"]
        assert data == v2_history[-1]


class TestPublicBarrierHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "users"]

    @freezegun.freeze_time("2020-03-02")
    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.save()
        self.public_barrier, _created = get_or_create_public_barrier(self.barrier)

    def test_location_history(self):
        self.public_barrier.country = "e0f682ac-5d95-e211-a939-e4115bead28a"
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "location"
        assert data["old_value"] == "France"
        assert data["new_value"] == "Georgia"

    def test_status_history(self):
        self.public_barrier.status = 4
        self.public_barrier.status_date = datetime.date(2020, 5, 1)
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "status"
        assert data["old_value"] == {
            "status": "1",
            "status_date": self.barrier.status_date,
            "is_resolved": False,
        }
        assert data["new_value"] == {
            "status": "4",
            "status_date": datetime.date(2020, 5, 1),
            "is_resolved": True,
        }

    def test_sectors_history(self):
        self.public_barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "sectors"
        assert data["old_value"]["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert data["new_value"]["sectors"] == ["9538cecc-5f95-e211-a939-e4115bead28a"]

    def test_public_view_status_history(self):
        self.barrier.public_eligibility = True
        self.barrier.public_eligibility_summary = "Allowed summary"
        self.barrier.save()
        self.public_barrier.public_view_status = PublicBarrierStatus.ALLOWED
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
            "public_eligibility": True,
            "public_eligibility_summary": "Allowed summary",
            "approvers_summary": "",
        }
        assert data["new_value"] == {
            "public_view_status": {
                "id": PublicBarrierStatus.ALLOWED,
                "name": PublicBarrierStatus.choices[PublicBarrierStatus.ALLOWED],
            },
            "public_eligibility": True,
            "public_eligibility_summary": "Allowed summary",
            "approvers_summary": "",
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

    def test_title_history(self):
        self.public_barrier.title = "New title"
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(
            barrier_id=self.barrier.pk
        )
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "title"
        assert data["old_value"] == ""
        assert data["new_value"] == "New title"


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

        v2_history = EconomicAssessment.get_history(barrier_id=self.barrier.pk)
        data = v2_history[-1]

        assert data["model"] == "economic_assessment"
        assert data["field"] == "explanation"
        assert data["old_value"] == "Some explanation"
        assert data["new_value"] == "New explanation"

    def test_rating_history(self):
        self.assessment.rating = "HIGH"
        self.assessment.save()

        v2_history = EconomicAssessment.get_history(barrier_id=self.barrier.pk)
        enrich_rating(v2_history)
        data = v2_history[-1]

        assert data["model"] == "economic_assessment"
        assert data["field"] == "rating"
        assert data["old_value"]["name"] == "Low"
        assert data["new_value"]["name"] == "High"

    def test_documents_history(self):
        self.assessment.documents.add("fdb0624e-a549-4f70-b9a2-68896e4d1141")

        v2_history = EconomicAssessment.get_history(barrier_id=self.barrier.pk)
        data = v2_history[-1]

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

        v2_history = EconomicAssessment.get_history(barrier_id=self.barrier.pk)
        data = v2_history[-1]

        assert data["model"] == "economic_assessment"
        assert data["field"] == "export_value"
        assert data["old_value"] == 40000
        assert data["new_value"] == 2222

    def test_import_market_size_history(self):
        self.assessment.import_market_size = 3333
        self.assessment.save()

        v2_history = EconomicAssessment.get_history(barrier_id=self.barrier.pk)
        data = v2_history[-1]

        assert data["model"] == "economic_assessment"
        assert data["field"] == "import_market_size"
        assert data["old_value"] == 20000
        assert data["new_value"] == 3333

    def test_value_to_economy_history(self):
        self.assessment.value_to_economy = 4444
        self.assessment.save()

        v2_history = EconomicAssessment.get_history(barrier_id=self.barrier.pk)
        data = v2_history[-1]

        assert data["model"] == "economic_assessment"
        assert data["field"] == "value_to_economy"
        assert data["old_value"] == 10000
        assert data["new_value"] == 4444


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

        items = BarrierProgressUpdate.get_history(barrier_id=self.barrier.pk)

        # Expect (from earliest to latest):
        # ON_TRACK set, no previous
        # ON_TRACK changes to DELAYED
        assert items[0]["old_value"] == {
            "status": None,
            "update": None,
            "next_steps": None,
        }
        assert items[0]["new_value"] == {
            "status": "ON_TRACK",
            "update": "Nothing Specific",
            "next_steps": "Finish writing these tests.",
        }
        assert items[1]["old_value"] == {
            "status": "ON_TRACK",
            "update": "Nothing Specific",
            "next_steps": "Finish writing these tests.",
        }
        assert items[1]["new_value"] == {
            "status": "DELAYED",
            "update": "Nothing Specific",
            "next_steps": "Get coffee.",
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

        items = BarrierProgressUpdate.get_history(barrier_id=self.barrier.pk)

        # Expect (from earliest to latest):
        # ON_TRACK set, no previous
        # ON_TRACK changes to DELAYED
        assert items[0]["old_value"] == {
            "status": None,
            "update": None,
            "next_steps": None,
        }
        assert items[0]["new_value"] == {
            "status": "ON_TRACK",
            "update": "Nothing Specific",
            "next_steps": "Finish writing these tests.",
        }
        assert items[1]["old_value"] == {
            "status": "ON_TRACK",
            "update": "Nothing Specific",
            "next_steps": "Finish writing these tests.",
        }
        assert items[1]["new_value"] == {
            "status": "DELAYED",
            "update": "Nothing Specific",
            "next_steps": "Finish writing these tests.",
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

        items = BarrierProgressUpdate.get_history(barrier_id=self.barrier.pk)

        assert items == [
            {
                "date": items[0]["date"],
                "field": "status",
                "model": "progress_update",
                "new_value": {
                    "next_steps": "Finish writing these tests.",
                    "status": "ON_TRACK",
                    "update": "Nothing Specific",
                },
                "old_value": {"next_steps": None, "status": None, "update": None},
                "user": None,
            },
            {
                "date": items[1]["date"],
                "field": "status",
                "model": "progress_update",
                "new_value": {
                    "next_steps": "Get coffee.",
                    "status": "DELAYED",
                    "update": "Nothing Specific",
                },
                "old_value": {
                    "next_steps": "Finish writing these tests.",
                    "status": "ON_TRACK",
                    "update": "Nothing Specific",
                },
                "user": None,
            },
            {
                "date": items[2]["date"],
                "field": "status",
                "model": "progress_update",
                "new_value": {
                    "next_steps": "Finish writing these tests.",
                    "status": "RISK_OF_DELAY",
                    "update": "Nothing Specific",
                },
                "old_value": {
                    "next_steps": "Get coffee.",
                    "status": "DELAYED",
                    "update": "Nothing Specific",
                },
                "user": None,
            },
        ]


class TestActionPlanHistory(APITestMixin, TestCase):
    fixtures = ["users", "barriers"]

    @freezegun.freeze_time("2020-03-02")
    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")

    def test_action_plan_no_user_history(self):
        action_plan = ActionPlan.objects.get(barrier=self.barrier)
        milestone = ActionPlanMilestoneFactory(action_plan=action_plan)
        action_plan_task = ActionPlanTaskFactory(milestone=milestone, assigned_to=None)
        action_plan_task.assigned_to = self.mock_user
        action_plan_task.save()

        task_history = ActionPlanTask.get_history(barrier_id=self.barrier)
        data = task_history[-1]

        # asserting that when the old value of assigned_to is None, the mock user is returned
        assert data["old_value"] == {
            "assigned_to__first_name": None,
            "assigned_to__last_name": None,
        }
        assert data["new_value"] == {
            "assigned_to__first_name": self.mock_user.first_name,
            "assigned_to__last_name": self.mock_user.last_name,
        }


class TestWTOProfileHistory(APITestMixin, TestCase):
    fixtures = ["users", "barriers"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")

    def test_wto_profile_status_history(self):

        WTOProfile.objects.create(
            barrier=self.barrier,
            wto_has_been_notified=False,
            wto_should_be_notified=False,
        )

        self.barrier.refresh_from_db()

        self.barrier.wto_profile.wto_has_been_notified = True
        self.barrier.wto_profile.wto_should_be_notified = True
        self.barrier.wto_profile.save()

        v2_history = WTOProfile.get_history(barrier_id=self.barrier.pk)
        enrich_wto_notified_status(v2_history)
        data = v2_history[-1]  # last item in history

        assert data["model"] == "wto_profile"
        assert data["field"] == "wto_notified_status"
        assert data["old_value"] == {
            "wto_has_been_notified": False,
            "wto_should_be_notified": False,
        }
        assert data["new_value"] == {
            "wto_has_been_notified": True,
            "wto_should_be_notified": True,
        }

    def test_wto_committee_notified_history(self):

        WTOProfileFactory(
            barrier=self.barrier,
        )

        self.barrier.refresh_from_db()

        self.barrier.wto_profile.committee_notified = WTOCommitteeFactory()
        self.barrier.wto_profile.save()

        v2_history = WTOProfile.get_history(barrier_id=self.barrier.pk)
        enrich_wto_notified_status(v2_history)
        enrich_committee_notified(v2_history)
        data = v2_history[-1]  # last item in history

        assert data["model"] == "wto_profile"
        assert data["field"] == "committee_notified"
        assert data["old_value"] is None
        assert data["new_value"] == {
            "id": str(self.barrier.wto_profile.committee_notified.id),
            "name": self.barrier.wto_profile.committee_notified.name,
        }

    def test_wto_committee_raised_in_history(self):

        WTOProfileFactory(
            barrier=self.barrier,
        )

        self.barrier.refresh_from_db()

        prev_committee_raised_in_id = self.barrier.wto_profile.committee_raised_in.id
        prev_committee_raised_in_name = (
            self.barrier.wto_profile.committee_raised_in.name
        )

        self.barrier.wto_profile.committee_raised_in = WTOCommitteeFactory()
        self.barrier.wto_profile.save()

        self.barrier.wto_profile.refresh_from_db()

        v2_history = WTOProfile.get_history(barrier_id=self.barrier.pk)
        enrich_wto_notified_status(v2_history)
        enrich_committee_raised_in(v2_history)
        data = v2_history[-1]

        assert data["model"] == "wto_profile"
        assert data["field"] == "committee_raised_in"

        assert data["old_value"] == {
            "id": str(prev_committee_raised_in_id),
            "name": prev_committee_raised_in_name,
        }
        assert data["new_value"] == {
            "id": str(self.barrier.wto_profile.committee_raised_in.id),
            "name": self.barrier.wto_profile.committee_raised_in.name,
        }
