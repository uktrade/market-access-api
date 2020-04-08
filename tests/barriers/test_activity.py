from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from api.assessment.models import Assessment
from api.barriers.models import BarrierInstance
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin
from api.interactions.models import Interaction


class TestActivityView(APITestMixin, TestCase):
    fixtures = ["categories", "documents", "users", "barriers"]

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
    def test_activity_endpoint(self):
        url = reverse("activity", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Barrier changes
        self.barrier.categories.add("109", "115")
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.problem_description = "New problem_description"
        self.barrier.export_country = "81756b9a-5d95-e211-a939-e4115bead28a"
        self.barrier.country_admin_areas = ["a88512e0-62d4-4808-95dc-d3beab05d0e9"]
        self.barrier.priority_id = 2
        self.barrier.product = "New product"
        self.barrier.status = 5
        self.barrier.problem_status = 1
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.source = "COMPANY"
        self.barrier.barrier_title = "New title"
        self.barrier.save()

        with freeze_time("2020-04-02"):
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
        fields = [(item["model"], item["field"]) for item in history]

        assert ("barrier", "priority") in fields
        assert ("barrier", "status") in fields
        assert ("barrier", "archived") in fields
        assert ("assessment", "impact") in fields
        assert ("assessment", "commercial_value") in fields
        assert ("assessment", "export_value") in fields
        assert ("assessment", "import_market_size") in fields
        assert ("assessment", "value_to_economy") in fields

        assert ("barrier", "categories") not in fields
        assert ("barrier", "companies") not in fields
        assert ("barrier", "problem_description") not in fields
        assert ("barrier", "location") not in fields
        assert ("barrier", "product") not in fields
        assert ("barrier", "problem_status") not in fields
        assert ("barrier", "sectors") not in fields
        assert ("barrier", "source") not in fields
        assert ("barrier", "barrier_title") not in fields
        assert ("assessment", "documents") not in fields
        assert ("assessment", "explanation") not in fields
        assert ("team_member", "user") not in fields
        assert ("note", "text") not in fields
        assert ("note", "documents") not in fields
