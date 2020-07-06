import datetime

from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from api.assessment.models import Assessment
from api.barriers.history import (
    AssessmentHistoryFactory,
    BarrierHistoryFactory,
    NoteHistoryFactory,
    PublicBarrierHistoryFactory,
    TeamMemberHistoryFactory,
)
from api.barriers.models import BarrierInstance, PublicBarrier
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin
from api.interactions.models import Interaction


class TestBarrierHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "categories", "users"]

    def setUp(self):
        self.barrier = BarrierInstance.objects.get(
            pk="c33dad08-b09c-4e19-ae1a-be47796a8882"
        )
        self.barrier.save()

    def test_archived_history(self):
        self.barrier.archive(
            user=self.user,
            reason="DUPLICATE",
            explanation="It was a duplicate"
        )

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "archived"
        assert data["old_value"] == {
            "archived": False,
            "unarchived_reason": None,
        }
        assert data["new_value"] == {
            "archived": True,
            "archived_reason": "DUPLICATE",
            "archived_explanation": "It was a duplicate",
        }

    def test_categories_history(self):
        self.barrier.categories.add("109", "115")

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "categories"
        assert data["old_value"] == []
        assert set(data["new_value"]) == {"109", "115"}

    def test_companies_history(self):
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "companies"
        assert data["old_value"] is None
        assert data["new_value"] == ["1", "2", "3"]

    def test_description_history(self):
        self.barrier.summary = "New summary"
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "summary"
        assert data["old_value"] == "Some summary"
        assert data["new_value"] == "New summary"

    def test_location_history(self):
        self.barrier.export_country = "81756b9a-5d95-e211-a939-e4115bead28a"
        self.barrier.country_admin_areas = ["a88512e0-62d4-4808-95dc-d3beab05d0e9"]

        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "location"
        assert data["old_value"] == {
            "country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "admin_areas": [],
        }
        assert data["new_value"] == {
            "country": "81756b9a-5d95-e211-a939-e4115bead28a",
            "admin_areas": ["a88512e0-62d4-4808-95dc-d3beab05d0e9"],
        }

    def test_priority_history(self):
        self.barrier.priority_id = 2
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "priority"
        assert data["old_value"] == {
            "priority": None,
            "priority_summary": None,
        }
        assert data["new_value"] == {
            "priority": "HIGH",
            "priority_summary": None,
        }

    def test_product_history(self):
        self.barrier.product = "New product"
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "product"
        assert data["old_value"] == "Some product"
        assert data["new_value"] == "New product"

    def test_status_history(self):
        self.barrier.status = 5
        self.barrier.status_summary = "Summary"
        self.barrier.sub_status = "UK_GOVT"
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "status"
        assert data["old_value"] == {
            "status": "1",
            "status_date": datetime.date(2019, 4, 9),
            "status_summary": None,
            "sub_status": None,
            "sub_status_other": None,
        }
        assert data["new_value"] == {
            "status": "5",
            "status_date": datetime.date(2019, 4, 9),
            "status_summary": "Summary",
            "sub_status": "UK_GOVT",
            "sub_status_other": None,
        }

    def test_scope_history(self):
        self.barrier.problem_status = 1
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "problem_status"
        assert data["old_value"] == 2
        assert data["new_value"] == 1

    def test_sectors_history(self):
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "sectors"
        assert data["old_value"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert data["new_value"] == ["9538cecc-5f95-e211-a939-e4115bead28a"]

    def test_source_history(self):
        self.barrier.source = "COMPANY"
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "source"
        assert data["old_value"] == {
            "source": "OTHER",
            "other_source": "Other source",
        }
        assert data["new_value"] == {
            "source": "COMPANY",
            "other_source": None,
        }

    def test_title_history(self):
        self.barrier.barrier_title = "New title"
        self.barrier.save()

        items = BarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "barrier"
        assert data["field"] == "barrier_title"
        assert data["old_value"] == "Some title"
        assert data["new_value"] == "New title"


class TestPublicBarrierHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "categories", "users"]

    def setUp(self):
        self.barrier = BarrierInstance.objects.get(
            pk="c33dad08-b09c-4e19-ae1a-be47796a8882"
        )
        self.barrier.save()

        self.public_barrier, created = PublicBarrier.objects.get_or_create(
            barrier=self.barrier,
            defaults={
                "status": self.barrier.status,
                "country": self.barrier.export_country,
                "sectors": self.barrier.sectors,
            }
        )
        if created:
            self.public_barrier.categories.set(self.barrier.categories.all())

    def test_pcategories_history(self):
        self.public_barrier.categories.add("109", "115")

        items = PublicBarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "categories"
        assert data["old_value"] == []
        assert set(data["new_value"]) == {"109", "115"}

    def test_status_history(self):
        self.public_barrier.status = 5
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "status"
        assert data["old_value"] == {
            "status": "1",
        }
        assert data["new_value"] == {
            "status": "5",
        }

    def test_sectors_history(self):
        self.public_barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "sectors"
        assert data["old_value"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert data["new_value"] == ["9538cecc-5f95-e211-a939-e4115bead28a"]

    def test_summary_history(self):
        self.public_barrier.summary = "New summary"
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "summary"
        assert data["old_value"] == None
        assert data["new_value"] == "New summary"

    def test_title_history(self):
        self.public_barrier.title = "New title"
        self.public_barrier.save()

        items = PublicBarrierHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "public_barrier"
        assert data["field"] == "title"
        assert data["old_value"] == None
        assert data["new_value"] == "New title"


class TestAssessmentHistory(APITestMixin, TestCase):
    fixtures = ["barriers", "documents", "users"]

    def setUp(self):
        self.barrier = BarrierInstance.objects.get(
            pk="c33dad08-b09c-4e19-ae1a-be47796a8882"
        )
        self.assessment = Assessment.objects.create(
            barrier=self.barrier,
            impact="LOW",
            explanation="Some explanation",
            value_to_economy=10000,
            import_market_size=20000,
            commercial_value=30000,
            export_value=40000,
        )

    def test_explanation_history(self):
        self.assessment.explanation = "New explanation"
        self.assessment.save()

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "explanation"
        assert data["old_value"] == "Some explanation"
        assert data["new_value"] == "New explanation"

    def test_impact_history(self):
        self.assessment.impact = "HIGH"
        self.assessment.save()

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "impact"
        assert data["old_value"] == "LOW"
        assert data["new_value"] == "HIGH"

    def test_documents_history(self):
        self.assessment.documents.add("fdb0624e-a549-4f70-b9a2-68896e4d1141")

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)

        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "documents"
        assert data["old_value"] == []
        assert data["new_value"] == [
            {
                "id": "fdb0624e-a549-4f70-b9a2-68896e4d1141",
                "name": "dog.jpg",
            }
        ]

    def test_commercial_value_history(self):
        self.assessment.commercial_value = 1111
        self.assessment.save()

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "commercial_value"
        assert data["old_value"] == 30000
        assert data["new_value"] == 1111

    def test_export_value_history(self):
        self.assessment.export_value = 2222
        self.assessment.save()

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "export_value"
        assert data["old_value"] == 40000
        assert data["new_value"] == 2222

    def test_import_market_size_history(self):
        self.assessment.import_market_size = 3333
        self.assessment.save()

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "import_market_size"
        assert data["old_value"] == 20000
        assert data["new_value"] == 3333

    def test_value_to_economy_history(self):
        self.assessment.value_to_economy = 4444
        self.assessment.save()

        items = AssessmentHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "assessment"
        assert data["field"] == "value_to_economy"
        assert data["old_value"] == 10000
        assert data["new_value"] == 4444


class TestNoteHistory(APITestMixin, TestCase):
    fixtures = ["documents", "users", "barriers"]

    def setUp(self):
        self.barrier = BarrierInstance.objects.get(
            pk="c33dad08-b09c-4e19-ae1a-be47796a8882"
        )
        self.barrier.save()
        self.note = Interaction.objects.create(
            barrier=self.barrier,
            kind="COMMENT",
            text="Original note",
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
        self.barrier = BarrierInstance.objects.get(
            pk="c33dad08-b09c-4e19-ae1a-be47796a8882"
        )
        self.barrier.save()

    def test_team_member_history(self):
        TeamMember.objects.create(
            barrier=self.barrier,
            user=self.user,
            role="Contributor"
        )

        items = TeamMemberHistoryFactory.get_history_items(barrier_id=self.barrier.pk)
        data = items[-1].data

        assert data["model"] == "team_member"
        assert data["field"] == "user"
        assert data["old_value"] is None
        assert data["new_value"] == {
            "user": {"id": 4, "name": "Testo Useri"},
            "role": "Contributor",
        }


class TestHistoryView(APITestMixin, TestCase):
    fixtures = ["categories", "documents", "users", "barriers"]

    @freeze_time("2020-03-02")
    def setUp(self):
        self.barrier = BarrierInstance.objects.get(
            pk="c33dad08-b09c-4e19-ae1a-be47796a8882"
        )
        self.barrier.save()

        self.assessment = Assessment.objects.create(
            barrier=self.barrier,
            impact="LOW",
            explanation="Some explanation",
            value_to_economy=10000,
            import_market_size=20000,
            commercial_value=30000,
            export_value=40000,
        )

        self.note = Interaction.objects.create(
            barrier=self.barrier,
            kind="COMMENT",
            text="Original note",
        )

    @freeze_time("2020-04-01")
    def test_history_endpoint(self):
        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Barrier changes
        self.barrier.categories.add("109", "115")
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.summary = "New summary"
        self.barrier.export_country = "81756b9a-5d95-e211-a939-e4115bead28a"
        self.barrier.country_admin_areas = ["a88512e0-62d4-4808-95dc-d3beab05d0e9"]
        self.barrier.priority_id = 2
        self.barrier.product = "New product"
        self.barrier.status = 5
        self.barrier.status_summary = "Summary"
        self.barrier.sub_status = "UK_GOVT"
        self.barrier.problem_status = 1
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.source = "COMPANY"
        self.barrier.barrier_title = "New title"
        self.barrier.save()

        self.barrier.archive(
            user=self.user,
            reason="DUPLICATE",
            explanation="It was a duplicate"
        )

        # Note changes
        self.note.documents.add("eda7ee4e-4786-4507-a0ed-05a10169764b")
        self.note.text = "Edited note"
        self.note.save()

        # Team Member changes
        TeamMember.objects.create(
            barrier=self.barrier,
            user=self.user,
            role="Contributor"
        )

        # Assessment changes
        self.assessment.explanation = "New explanation"
        self.assessment.impact = "HIGH"
        self.assessment.documents.add("fdb0624e-a549-4f70-b9a2-68896e4d1141")
        self.assessment.commercial_value = 1111
        self.assessment.export_value = 2222
        self.assessment.import_market_size = 3333
        self.assessment.value_to_economy = 4444
        self.assessment.save()

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "archived",
            "old_value": {
                "archived": False,
                "unarchived_reason": None
            },
            "new_value": {
                "archived": True,
                "archived_reason": "DUPLICATE",
                "archived_explanation": "It was a duplicate"
            },
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "categories",
            "old_value": [],
            "new_value": ["109", "115"],
            "user": None,
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "location",
            "old_value": {
                "country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "admin_areas": []
            },
            "new_value": {
                "country": "81756b9a-5d95-e211-a939-e4115bead28a",
                "admin_areas": ["a88512e0-62d4-4808-95dc-d3beab05d0e9"]
            },
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "summary",
            "old_value": "Some summary",
            "new_value": "New summary",
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "status",
            "old_value": {
                "status": "1",
                "status_date": "2019-04-09",
                "status_summary": None,
                "sub_status": None,
                "sub_status_other": None,
            },
            "new_value": {
                "status": "5",
                "status_date": "2019-04-09",
                "status_summary": "Summary",
                "sub_status": "UK_GOVT",
                "sub_status_other": None,
            },
            "user": None,
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "barrier_title",
            "old_value": "Some title",
            "new_value": "New title",
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "priority",
            "old_value": {
                "priority": None,
                "priority_summary": None,
            },
            "new_value": {
                "priority": "HIGH",
                "priority_summary": None,
            },
            "user": None,
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "source",
            "old_value": {
                "source": "OTHER",
                "other_source": "Other source",
            },
            "new_value": {
                "source": "COMPANY",
                "other_source": None,
            },
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "problem_status",
            "old_value": 2,
            "new_value": 1,
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "product",
            "old_value": "Some product",
            "new_value": "New product",
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "sectors",
            "old_value": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "new_value": ["9538cecc-5f95-e211-a939-e4115bead28a"],
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "companies",
            "old_value": None,
            "new_value": ["1", "2", "3"],
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "note",
            "field": "text",
            "old_value": "Original note",
            "new_value": "Edited note",
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "note",
            "field": "documents",
            "old_value": [],
            "new_value": [{
                "id": "eda7ee4e-4786-4507-a0ed-05a10169764b",
                "name": "cat.jpg"
            }],
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "assessment",
            "field": "value_to_economy",
            "old_value": 10000,
            "new_value": 4444,
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "assessment",
            "field": "import_market_size",
            "old_value": 20000,
            "new_value": 3333,
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "assessment",
            "field": "commercial_value",
            "old_value": 30000,
            "new_value": 1111,
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "assessment",
            "field": "export_value",
            "old_value": 40000,
            "new_value": 2222,
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "assessment",
            "field": "documents",
            "old_value": [],
            "new_value": [{
                "id": "fdb0624e-a549-4f70-b9a2-68896e4d1141",
                "name": "dog.jpg"
            }],
            "user": None
        } in history

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "team_member",
            "field": "user",
            "old_value": None,
            "new_value": {
                "user": {
                    "id": 4,
                    "name": "Testo Useri"
                },
                "role": "Contributor"
            },
            "user": None
        } in history
