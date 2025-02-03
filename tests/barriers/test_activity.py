from unittest.mock import patch

import freezegun
from django.test import TestCase
from notifications_python_client.notifications import NotificationsAPIClient
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin
from api.interactions.models import Interaction

from ..assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
    ResolvabilityAssessmentFactory,
    StrategicAssessmentFactory,
)

freezegun.configure(extend_ignore_list=["transformers"])


class TestActivityView(APITestMixin, TestCase):
    fixtures = ["documents", "users", "barriers"]

    @freezegun.freeze_time("2020-03-01")
    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.draft = False
        self.barrier.save()

        self.note = Interaction.objects.create(
            barrier=self.barrier,
            kind="COMMENT",
            text="Original note",
            created_by=self.mock_user,
        )

    @freezegun.freeze_time("2020-04-01")
    def test_activity_endpoint(self):
        url = reverse("activity", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Barrier changes
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.summary = "New summary"
        self.barrier.country = "81756b9a-5d95-e211-a939-e4115bead28a"  # USA
        self.barrier.admin_areas = [
            "a88512e0-62d4-4808-95dc-d3beab05d0e9"
        ]  # California
        self.barrier.priority_id = 2
        self.barrier.product = "New product"
        self.barrier.status = 5
        self.barrier.term = 1
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.source = "COMPANY"
        self.barrier.title = "New title"
        self.barrier.save()

        with freezegun.freeze_time("2020-04-02"):
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
                scale=5,
            )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        history = response.json()["history"]
        fields = [(item["model"], item["field"]) for item in history]

        assert ("barrier", "priority") in fields
        assert ("barrier", "status") in fields
        assert ("barrier", "archived") in fields
        assert ("economic_assessment", "rating") in fields
        assert ("economic_impact_assessment", "impact") in fields
        assert ("resolvability_assessment", "time_to_resolve") in fields
        assert ("strategic_assessment", "scale") in fields

        assert ("barrier", "companies") not in fields
        assert ("barrier", "summary") not in fields
        assert ("barrier", "location") not in fields
        assert ("barrier", "product") not in fields
        assert ("barrier", "term") not in fields
        assert ("barrier", "sectors") not in fields
        assert ("barrier", "source") not in fields
        assert ("barrier", "title") not in fields
        assert ("economic_assessment", "explanation") not in fields
        assert ("economic_impact_assessment", "explanation") not in fields
        assert ("resolvability_assessment", "explanation") not in fields
        assert ("strategic_assessment", "hmg_strategy") not in fields
        assert ("team_member", "user") not in fields
        assert ("note", "text") not in fields
        assert ("note", "documents") not in fields
