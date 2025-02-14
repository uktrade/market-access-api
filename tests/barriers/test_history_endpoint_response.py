import datetime
import random
from unittest import skip
from unittest.mock import patch

import freezegun
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import Barrier, BarrierTopPrioritySummary
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin
from api.metadata.constants import (
    BARRIER_SOURCE,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_DIRECTION_CHOICES,
)
from api.metadata.models import BarrierPriority, Organisation
from tests.assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
    ResolvabilityAssessmentFactory,
    StrategicAssessmentFactory,
)
from tests.barriers.factories import CommodityFactory
from tests.metadata.factories import BarrierPolicyTeamFactory, BarrierTagFactory

freezegun.configure(extend_ignore_list=["transformers"])


class TestHistoryEndpointResponse(APITestMixin, TestCase):
    fixtures = ["documents", "users", "barriers"]

    @freezegun.freeze_time("2020-03-02")
    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        # need to force a previous history item into existence to get history endpoint to work :-/
        self.barrier.draft = False
        self.barrier.title = "Force history entry"
        self.barrier.save()

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint(self):
        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_archived(self):
        initial_archived_state = self.barrier.archived
        initial_unarchived_reason = self.barrier.unarchived_reason
        archived_reason = "DUPLICATE"
        archived_explanation = "It was a duplicate"
        self.barrier.archive(
            user=self.user, reason=archived_reason, explanation=archived_explanation
        )
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]
        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "archived",
            "old_value": {
                "archived": initial_archived_state,
                "archived_reason": "",
                "archived_explanation": "",
                "unarchived_reason": "",
            },
            "new_value": {
                "archived": True,
                "archived_reason": archived_reason,
                "archived_explanation": archived_explanation,
                "unarchived_reason": "",
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_commercial_value(self):
        initial_commercial_value = self.barrier.commercial_value
        expected_commercial_value = 1111
        self.barrier.commercial_value = expected_commercial_value
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "commercial_value",
            "old_value": initial_commercial_value,
            "new_value": expected_commercial_value,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_commercial_value_explanation(self):
        initial_commercial_value_explanation = self.barrier.commercial_value_explanation
        expected_commercial_value_explanation = "CV explanation"
        self.barrier.commercial_value_explanation = (
            expected_commercial_value_explanation
        )
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "commercial_value_explanation",
            "old_value": initial_commercial_value_explanation,
            "new_value": expected_commercial_value_explanation,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_commodities(self):
        initial_commodities = list(self.barrier.commodities.all())
        expected_commodity = CommodityFactory(
            code="2105000000", description="Ice cream"
        )
        self.barrier.commodities.add(expected_commodity)
        # M2M field with intermediate model needs explicit save() after add()
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "commodities",
            "old_value": initial_commodities,
            "new_value": [
                {
                    "code": "",
                    "country": None,
                    "commodity": {
                        "code": expected_commodity.code,
                        "version": expected_commodity.version,
                        "description": expected_commodity.description,
                        "full_description": expected_commodity.full_description,
                    },
                    "trading_bloc": None,
                }
            ],
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_companies(self):
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "companies",
            "old_value": [],
            "new_value": ["1", "2", "3"],
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_economic_assessment_eligibility(self):
        initial_economic_assessment_eligibility = (
            self.barrier.economic_assessment_eligibility
        )
        expected_economic_assessment_eligibility = (
            not initial_economic_assessment_eligibility
        )
        self.barrier.economic_assessment_eligibility = (
            expected_economic_assessment_eligibility
        )
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "economic_assessment_eligibility",
            "old_value": initial_economic_assessment_eligibility,
            "new_value": expected_economic_assessment_eligibility,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_economic_assessment_eligibility_summary(self):
        initial_economic_assessment_eligibility_summary = (
            self.barrier.economic_assessment_eligibility_summary
        )
        expected_economic_assessment_eligibility_summary = f"""
        {initial_economic_assessment_eligibility_summary}
        replaced by new economic assessment eligibility summary"
        """
        self.barrier.economic_assessment_eligibility_summary = (
            expected_economic_assessment_eligibility_summary
        )
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "economic_assessment_eligibility_summary",
            "old_value": initial_economic_assessment_eligibility_summary,
            "new_value": expected_economic_assessment_eligibility_summary,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_economic_assessment_rating(self):
        economic_assessment = EconomicAssessmentFactory(
            barrier=self.barrier,
            rating="LOW",
        )

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "economic_assessment",
            "field": "rating",
            "old_value": None,
            "new_value": {
                "id": economic_assessment.rating,
                "name": economic_assessment.get_rating_display(),
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_economic_impact_assessment_impact(self):
        economic_assessment = EconomicAssessmentFactory(
            barrier=self.barrier,
            rating="LOW",
        )
        economic_impact_assessment = EconomicImpactAssessmentFactory(
            economic_assessment=economic_assessment,
            barrier=economic_assessment.barrier,
            impact=4,
        )

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "economic_impact_assessment",
            "field": "impact",
            "old_value": None,
            "new_value": {
                "code": economic_impact_assessment.impact,
                "name": economic_impact_assessment.get_impact_display(),
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_estimated_resolution_date(self):
        initial_estimated_resolution_date = self.barrier.estimated_resolution_date
        expected_estimated_resolution_date = datetime.date(year=2030, month=12, day=25)
        self.barrier.estimated_resolution_date = expected_estimated_resolution_date
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "estimated_resolution_date",
            "old_value": initial_estimated_resolution_date,
            "new_value": expected_estimated_resolution_date.isoformat(),
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_is_summary_sensitive(self):
        initial_is_summary_sensitive = self.barrier.is_summary_sensitive
        expected_is_summary_sensitive = not initial_is_summary_sensitive
        self.barrier.is_summary_sensitive = expected_is_summary_sensitive
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "is_summary_sensitive",
            "old_value": initial_is_summary_sensitive,
            "new_value": expected_is_summary_sensitive,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_location(self):
        self.barrier.country = "81756b9a-5d95-e211-a939-e4115bead28a"  # USA
        self.barrier.admin_areas = [
            "a88512e0-62d4-4808-95dc-d3beab05d0e9"
        ]  # California
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        location_history = [item for item in history if item["field"] == "location"]
        assert len(location_history) == 1
        assert location_history[0]["old_value"] == "France"
        assert location_history[0]["new_value"] == "California (United States)"

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_organisations(self):
        # ensure no organisations for previous history entry
        self.barrier.organisations.clear()
        self.barrier.save()
        expected_organisation_name = "Department for International Trade"
        expected_organisation = Organisation.objects.get(
            name=expected_organisation_name
        )
        self.barrier.organisations.add(expected_organisation)
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "organisations",
            "old_value": [],
            "new_value": [expected_organisation.pk],
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_priority(self):
        initial_priority = self.barrier.priority
        self.barrier.priority = BarrierPriority.objects.get(code="HIGH")
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "priority",
            "old_value": {
                "priority": initial_priority.code,
                "priority_summary": "",
            },
            "new_value": {
                "priority": self.barrier.priority.code,
                "priority_summary": "",
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_product(self):
        self.barrier.product = "New product"
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "product",
            "old_value": "Some product",
            "new_value": "New product",
            "user": None,
        } in history

    @skip("Not recorded… yet")
    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_public_eligibility(self):
        initial_public_eligibility = self.barrier.public_eligibility
        expected_public_eligibility = not initial_public_eligibility
        self.barrier.public_eligibility = expected_public_eligibility
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "public_eligibility",
            "old_value": initial_public_eligibility,
            "new_value": expected_public_eligibility,
            "user": None,
        } in history

    @skip("Not recorded… yet")
    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_public_eligibility_postponed(self):
        initial_public_eligibility_postponed = self.barrier.public_eligibility_postponed
        expected_public_eligibility_postponed = not initial_public_eligibility_postponed
        self.barrier.public_eligibility_postponed = (
            expected_public_eligibility_postponed
        )
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "public_eligibility_postponed",
            "old_value": initial_public_eligibility_postponed,
            "new_value": expected_public_eligibility_postponed,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_public_eligibility_summary(self):
        initial_public_eligibility_summary = self.barrier.public_eligibility_summary
        expected_public_eligibility_summary = "New public eligibility summary"
        self.barrier.public_eligibility_summary = expected_public_eligibility_summary
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "public_eligibility_summary",
            "old_value": initial_public_eligibility_summary,
            "new_value": expected_public_eligibility_summary,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_resolvability_assessment_effort_to_resolve(self):
        resolvability_assessment = ResolvabilityAssessmentFactory(
            barrier=self.barrier,
            time_to_resolve=4,
            effort_to_resolve=1,
        )

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "resolvability_assessment",
            "field": "effort_to_resolve",
            "old_value": None,
            "new_value": {
                "id": resolvability_assessment.effort_to_resolve,
                "name": resolvability_assessment.get_effort_to_resolve_display(),
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_resolvability_assessment_time_to_resolve(self):
        resolvability_assessment = ResolvabilityAssessmentFactory(
            barrier=self.barrier,
            time_to_resolve=4,
            effort_to_resolve=1,
        )

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "resolvability_assessment",
            "field": "time_to_resolve",
            "old_value": None,
            "new_value": {
                "id": resolvability_assessment.time_to_resolve,
                "name": resolvability_assessment.get_time_to_resolve_display(),
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_sectors(self):
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "sectors",
            "old_value": {
                "all_sectors": None,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
            },
            "new_value": {
                "all_sectors": None,
                "sectors": ["9538cecc-5f95-e211-a939-e4115bead28a"],
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_source(self):
        self.barrier.source = BARRIER_SOURCE.COMPANY
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "source",
            "old_value": {
                "source": BARRIER_SOURCE.OTHER,
                "other_source": "Other source",
            },
            "new_value": {
                "source": BARRIER_SOURCE.COMPANY,
                "other_source": "",
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_status(self):
        initial_status = self.barrier.status
        initial_status_summary = self.barrier.status_summary
        initial_sub_status = self.barrier.sub_status
        self.barrier.status = 5
        self.barrier.status_summary = "Summary"
        self.barrier.sub_status = "UK_GOVT"
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "status",
            "old_value": {
                "status": str(initial_status),
                "status_date": "2019-04-09",
                "status_summary": initial_status_summary,
                "sub_status": initial_sub_status,
                "sub_status_other": "",
            },
            "new_value": {
                "status": str(self.barrier.status),
                "status_date": "2019-04-09",
                "status_summary": self.barrier.status_summary,
                "sub_status": self.barrier.sub_status,
                "sub_status_other": "",
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_strategic_assessment(self):
        strategic_assessment = StrategicAssessmentFactory(
            barrier=self.barrier,
            scale=3,
        )

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "strategic_assessment",
            "field": "scale",
            "old_value": None,
            "new_value": {
                "id": strategic_assessment.scale,
                "name": strategic_assessment.get_scale_display(),
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_summary(self):
        initial_summary = self.barrier.summary
        self.barrier.summary = "New summary"
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "summary",
            "old_value": initial_summary,
            "new_value": self.barrier.summary,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_tags(self):
        initial_tags = list(self.barrier.tags.all())
        expected_tag = BarrierTagFactory(title="brouhaha")
        self.barrier.tags.add(expected_tag)

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "tags",
            "old_value": initial_tags,
            "new_value": [expected_tag.id],
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_policy_teams(self):
        initial_policy_teams = list(self.barrier.policy_teams.all())
        expected_policy_team = BarrierPolicyTeamFactory(title="testing policy teams")
        self.barrier.policy_teams.add(expected_policy_team)

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "policy_teams",
            "old_value": initial_policy_teams,
            "new_value": [expected_policy_team.id],
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_team_member(self):
        team_member = TeamMember.objects.create(
            barrier=self.barrier, user=self.user, role="Contributor"
        )

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "team_member",
            "field": "user",
            "old_value": None,
            "new_value": {
                "user": {
                    "id": team_member.user.id,
                    "name": f"{team_member.user.first_name} {team_member.user.last_name}",
                },
                "role": team_member.role,
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_term(self):
        self.barrier.term = 1
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "term",
            "old_value": 2,
            "new_value": 1,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_title(self):
        initial_title = self.barrier.title
        self.barrier.title = "New title"
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "title",
            "old_value": initial_title,
            "new_value": self.barrier.title,
            "user": None,
        } in history

    @patch("api.barriers.signals.handlers.send_top_priority_notification")
    def test_history_endpoint_has_top_priority_approval_pending(self, _):
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.NONE
        self.barrier.save()
        BarrierTopPrioritySummary.objects.create(
            top_priority_summary_text="please approve me", barrier=self.barrier
        )
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.NONE
        self.barrier.save()

        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING
        self.barrier.save()

        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.RESOLVED
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert history == [
            {
                "date": history[0]["date"],
                "field": "top_priority_summary_text",
                "model": "barrier_top_priority_summary",
                "new_value": "please approve me",
                "old_value": None,
                "user": None,
            },
            {
                "date": history[1]["date"],
                "field": "top_priority_status",
                "model": "barrier",
                "new_value": {
                    "reason": "please approve me",
                    "value": "Top 100 Approval Pending",
                },
                "old_value": {"reason": "", "value": "Removed"},
                "user": None,
            },
            {
                "date": history[2]["date"],
                "field": "top_priority_status",
                "model": "barrier",
                "new_value": {
                    "reason": "please approve me",
                    "value": "Top 100 Priority Resolved",
                },
                "old_value": {
                    "reason": "please approve me",
                    "value": "Top 100 Approval Pending",
                },
                "user": None,
            },
        ]

    @patch("api.barriers.signals.handlers.send_top_priority_notification")
    def test_history_endpoint_has_top_priority_approved(self, _):
        # V2 tested
        BarrierTopPrioritySummary.objects.create(
            top_priority_summary_text="please approve me", barrier=self.barrier
        )
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING
        self.barrier.save()
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVED
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert history[-1] == {
            "date": history[-1]["date"],
            "model": "barrier",
            "field": "top_priority_status",
            "old_value": {
                "value": "Top 100 Approval Pending",
                "reason": "please approve me",
            },
            "new_value": {
                "value": "Top 100 Priority",
                "reason": "please approve me",
            },
            "user": None,
        }

    @patch("api.barriers.signals.handlers.send_top_priority_notification")
    def test_history_endpoint_has_top_priority_removal_pending(self, _):
        # V2 tested
        BarrierTopPrioritySummary.objects.create(
            top_priority_summary_text="First Summary", barrier=self.barrier
        )
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.APPROVED
        self.barrier.save()
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING
        self.barrier.top_priority_rejection_summary = "you have been rejected"
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert history[-1] == {
            "date": history[-1]["date"],
            "model": "barrier",
            "field": "top_priority_status",
            "old_value": {
                "value": "Top 100 Priority",
                "reason": "First Summary",
            },
            "new_value": {
                "value": "Top 100 Removal Pending",
                "reason": "First Summary",
            },
            "user": None,
        }

    @patch("api.barriers.signals.handlers.send_top_priority_notification")
    def test_history_endpoint_has_top_priority_removed(self, _):
        # V2 tested
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING
        self.barrier.save()

        summary = BarrierTopPrioritySummary.objects.create(
            top_priority_summary_text="Removal Pending", barrier=self.barrier
        )
        self.barrier.top_priority_status = TOP_PRIORITY_BARRIER_STATUS.NONE
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history_1 = response.json()["history"]

        assert history_1[-1] == {
            "date": history_1[-1]["date"],
            "field": "top_priority_status",
            "model": "barrier",
            "new_value": {"reason": "Removal Pending", "value": "Removed"},
            "old_value": {"reason": "", "value": "Top 100 Removal Pending"},
            "user": None,
        }
        summary.top_priority_summary_text = "Rejected"
        summary.save()
        response = self.api_client.get(url)
        history_2 = response.json()["history"]

        assert history_2[-2] == history_1[-1]
        assert history_2[-1] == {
            "date": history_2[-1]["date"],
            "field": "top_priority_summary_text",
            "model": "barrier_top_priority_summary",
            "new_value": "Rejected",
            "old_value": "Removal Pending",
            "user": None,
        }

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_trade_category(self):
        self.barrier.trade_category = "GOODS"
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "trade_category",
            "old_value": None,
            "new_value": {
                "id": "GOODS",
                "name": "Goods",
            },
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_has_trade_direction(self):
        initial_trade_direction = self.barrier.trade_direction
        expected_trade_direction = random.choice(
            [
                choice[0]
                for choice in TRADE_DIRECTION_CHOICES
                if choice[0] != initial_trade_direction
            ]
        )
        self.barrier.trade_direction = expected_trade_direction
        self.barrier.save()

        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier",
            "field": "trade_direction",
            "old_value": initial_trade_direction,
            "new_value": expected_trade_direction,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_barrier_top_priority_summary_creation(self):
        new_summary = BarrierTopPrioritySummary.objects.create(
            barrier=self.barrier,
            top_priority_summary_text="please approve me",
        )
        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]
        assert len(history) == 1
        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier_top_priority_summary",
            "field": "top_priority_summary_text",
            "old_value": None,
            "new_value": new_summary.top_priority_summary_text,
            "user": None,
        } in history

    @freezegun.freeze_time("2020-04-01")
    def test_history_endpoint_barrier_top_priority_summary_modification(self):
        new_summary = BarrierTopPrioritySummary.objects.create(
            barrier=self.barrier,
            top_priority_summary_text="please approve me",
        )
        new_summary.top_priority_summary_text = "please approve me edit 1"
        new_summary.save()
        url = reverse("history", kwargs={"pk": self.barrier.pk})
        response = self.api_client.get(url)
        history = response.json()["history"]
        assert len(history) == 2

        assert {
            "date": "2020-04-01T00:00:00Z",
            "model": "barrier_top_priority_summary",
            "field": "top_priority_summary_text",
            "old_value": "please approve me",
            "new_value": new_summary.top_priority_summary_text,
            "user": None,
        } in history
