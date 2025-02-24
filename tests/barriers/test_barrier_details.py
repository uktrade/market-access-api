import logging
from datetime import date, datetime, timedelta

import freezegun
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.helpers import get_team_members
from api.barriers.models import (
    Barrier,
    BarrierProgressUpdate,
    ProgrammeFundProgressUpdate,
)
from api.core.test_utils import APITestMixin
from api.metadata.constants import PROGRESS_UPDATE_CHOICES, TOP_PRIORITY_BARRIER_STATUS
from api.metadata.models import Organisation, PolicyTeam
from api.metadata.serializers import PolicyTeamSerializer
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import OrganisationFactory

logger = logging.getLogger(__name__)

freezegun.configure(extend_ignore_list=["transformers"])


class TestBarrierDetails(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory()
        self.url = reverse("get-barrier", kwargs={"pk": self.barrier.id})

    def test_get_barrier_details(self):
        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]

    def test_barrier_detail_by_code(self):
        url = reverse("barrier_detail_code", kwargs={"code": self.barrier.code})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert str(self.barrier.id) == response.data["id"]

    def test_patch_barrier_status_to_resolved_in_full(self):
        assert 1 == self.barrier.status
        status_date = "2018-09-10"
        status_summary = "some status summary"
        resolved_in_full = 4

        url = reverse("resolve-in-full", kwargs={"pk": self.barrier.id})
        payload = {
            "status_date": status_date,
            "status_summary": status_summary,
        }
        response = self.api_client.put(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert resolved_in_full == self.barrier.status
        assert status_date == self.barrier.status_date.strftime("%Y-%m-%d")
        assert status_summary == self.barrier.status_summary

    @freezegun.freeze_time("2020-02-22")
    def test_unknown_barrier_endpoint_sets_status_to_unknown(self):
        assert 1 == self.barrier.status
        status_summary = "some status summary"
        unknown = 7

        url = reverse("unknown-barrier", kwargs={"pk": self.barrier.id})
        payload = {
            "status_summary": status_summary,
        }
        response = self.api_client.put(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert unknown == self.barrier.status
        assert "2020-02-22" == self.barrier.status_date.strftime("%Y-%m-%d")
        assert status_summary == self.barrier.status_summary

    @freezegun.freeze_time("2020-02-22")
    def test_open_in_progress_endpoint_sets_status_to_open_in_progress(self):
        assert 1 == self.barrier.status
        status_summary = "some status summary"
        open_in_progress = 2

        url = reverse("open-in-progress", kwargs={"pk": self.barrier.id})
        payload = {
            "status_summary": status_summary,
        }
        response = self.api_client.put(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert open_in_progress == self.barrier.status
        assert "2020-02-22" == self.barrier.status_date.strftime("%Y-%m-%d")
        assert status_summary == self.barrier.status_summary

    def test_patch_title(self):
        title = "Just a new title"
        payload = {"title": title}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert title == response.data["title"]

    def test_patch_estimated_resolution_date_doesnt_update(self):
        payload = {"estimated_resolution_date": datetime.today().date() + timedelta(days=41)}

        response = self.api_client.patch(self.url, format="json", data=payload)
        self.barrier.refresh_from_db()

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert self.barrier.estimated_resolution_date != payload["estimated_resolution_date"]

    def test_patch_barrier_country(self):
        payload = {"country": "82756b9a-5d95-e211-a939-e4115bead28a"}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert "82756b9a-5d95-e211-a939-e4115bead28a" == response.data["country"]["id"]

    def test_patch_barrier_trading_bloc(self):
        payload = {"trading_bloc": "TB00016"}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert "TB00016" == response.data["trading_bloc"]["code"]

    def test_patch_barrier_caused_by_trading_bloc(self):
        payload = {
            "country": "82756b9a-5d95-e211-a939-e4115bead28a",
            "caused_by_trading_bloc": True,
        }
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert response.data["caused_by_trading_bloc"] is True

    def test_patch_barrier_term(self):
        assert 1 == self.barrier.term

        test_parameters = [
            {"term": None, "status_code": status.HTTP_200_OK, "expected_term": None},
            {"term": 2, "status_code": status.HTTP_200_OK, "expected_term": 2},
            {"term": 1, "status_code": status.HTTP_200_OK, "expected_term": 1},
            {"term": 0, "status_code": status.HTTP_400_BAD_REQUEST, "expected_term": 1},
            {
                "term": "ahoy!",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "expected_term": 1,
            },
            {
                "term": "987",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "expected_term": 1,
            },
        ]

        for tp in test_parameters:
            with self.subTest(tp=tp):
                payload = {
                    "term": tp["term"],
                }
                response = self.api_client.patch(self.url, format="json", data=payload)

                self.barrier.refresh_from_db()
                assert tp["status_code"] == response.status_code, f"Test params: {tp}"
                assert tp["expected_term"] == self.barrier.term, f"Test params: {tp}"

    def test_patch_barrier_to_affect_all_sectors(self):
        assert not self.barrier.all_sectors
        assert 1 == len(self.barrier.sectors)

        payload = {"all_sectors": True}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert response.data["all_sectors"] is True
        assert self.barrier.sectors == [
            sector["id"] for sector in response.data["sectors"]
        ]

    def test_policy_team_management(self):
        policy_team1 = PolicyTeam.objects.create(
            pk=100, title="Test Title", description="Test Description"
        )
        policy_team2 = PolicyTeam.objects.create(
            pk=101, title="Test Title", description="Test Description"
        )

        assert self.barrier.policy_teams.count() == 0

        response = self.api_client.patch(
            self.url, format="json", data={"policy_teams": [policy_team1.id]}
        )

        assert status.HTTP_200_OK == response.status_code
        assert (
            response.data["policy_teams"]
            == PolicyTeamSerializer([policy_team1], many=True).data
        )

        response = self.api_client.patch(
            self.url,
            format="json",
            data={"policy_teams": [policy_team1.id, policy_team2.id]},
        )

        assert status.HTTP_200_OK == response.status_code
        assert (
            response.data["policy_teams"]
            == PolicyTeamSerializer([policy_team1, policy_team2], many=True).data
        )

        response = self.api_client.patch(
            self.url, format="json", data={"policy_teams": []}
        )

        assert status.HTTP_200_OK == response.status_code
        assert response.data["policy_teams"] == []

    def test_update_barrier_adds_user_as_contributor(self):
        """Users who edit a barrier should be  added as a Contributor automatically."""
        assert not get_team_members(self.barrier)

        payload = {"title": "Wibble wobble"}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        team_members = get_team_members(self.barrier)
        assert 1 == team_members.count()
        assert "Contributor" == team_members.first().role

    def test_add_barrier_government_organisations(self):
        assert 0 == self.barrier.organisations.count()

        payload = {"government_organisations": ("1", "2")}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == len(response.data["government_organisations"])
        assert {1, 2} == set([org.id for org in self.barrier.government_organisations])

    def test_replace_barrier_government_organisations(self):
        org1 = Organisation.objects.get(id=1)
        org2 = Organisation.objects.get(id=2)
        org3 = Organisation.objects.get(id=3)
        self.barrier.organisations.add(org1, org2)

        assert 2 == self.barrier.government_organisations.count()

        payload = {"government_organisations": ("3",)}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == len(response.data["government_organisations"])
        assert org3.id == response.data["government_organisations"][0]["id"]
        assert 1 == self.barrier.government_organisations.count()
        assert org3 == self.barrier.government_organisations.first()

    def test_flush_barrier_government_organisations(self):
        org1 = Organisation.objects.get(id=1)
        self.barrier.organisations.add(org1)

        self.barrier.refresh_from_db()
        assert 1 == self.barrier.government_organisations.count()

        payload = {"government_organisations": ()}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert not response.data["government_organisations"]
        assert 0 == self.barrier.government_organisations.count()

    def test_flushing_government_organisations_leaves_other_organisations_intact(self):
        org1 = OrganisationFactory(name="Wibble", organisation_type=0)
        org2 = Organisation.objects.get(id=1)
        self.barrier.organisations.add(org1, org2)

        self.barrier.refresh_from_db()
        assert 2 == self.barrier.organisations.count()
        assert 1 == self.barrier.government_organisations.count()

        payload = {"government_organisations": ()}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert not response.data["government_organisations"]
        assert 0 == self.barrier.government_organisations.count()
        assert 1 == self.barrier.organisations.count()
        assert org1 == self.barrier.organisations.first()

    def test_has_value_for_is_top_priority(self):
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        serialised_data = response.data
        assert "is_top_priority" in serialised_data.keys()

    def test_value_for_is_top_priority_is_bool(self):
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        serialised_data = response.data
        assert "is_top_priority" in serialised_data.keys() and isinstance(
            serialised_data["is_top_priority"], bool
        )

    def test_is_top_priority_barrier(self):

        # Left: top_priority_status - Right: expected is_top_priority value
        top_priority_status_to_is_top_priority_map = {
            TOP_PRIORITY_BARRIER_STATUS.APPROVED: True,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING: True,
            TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING: False,
            TOP_PRIORITY_BARRIER_STATUS.NONE: False,
        }

        for (
            top_priority_status,
            is_top_priority,
        ) in top_priority_status_to_is_top_priority_map.items():
            barrier = BarrierFactory(top_priority_status=top_priority_status)
            url = reverse("get-barrier", kwargs={"pk": barrier.id})
            response = self.api_client.get(url)
            assert status.HTTP_200_OK == response.status_code
            serialised_data = response.data
            assert serialised_data["top_priority_status"] == top_priority_status
            assert (
                "is_top_priority" in serialised_data.keys()
                and serialised_data["is_top_priority"] is is_top_priority
            )

    def test_top_100_progress_updates(self):
        update_count = 3
        for i in range(0, update_count):
            BarrierProgressUpdate.objects.create(
                barrier=self.barrier,
                status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
                update=f"Update value {i}",
                next_steps=f"Next steps value {i}",
                created_on=datetime.now() + timedelta(hours=i),
            )
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert "progress_updates" in response_data
        assert len(response_data["progress_updates"]) == update_count
        assert response_data["progress_updates"][0]["message"] == "Update value 2"

    def test_programme_fund_progress_updates(self):
        update_count = 3
        for i in range(0, update_count):
            ProgrammeFundProgressUpdate.objects.create(
                barrier=self.barrier,
                milestones_and_deliverables=f"Milestones_and_deliverables value {i}",
                expenditure=f"Expenditure value {i}",
                created_on=datetime.now() + timedelta(hours=i),
            )
        response = self.api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert "programme_fund_progress_updates" in response_data
        assert len(response_data["programme_fund_progress_updates"]) == update_count
        assert (
            response_data["programme_fund_progress_updates"][0][
                "milestones_and_deliverables"
            ]
            == "Milestones_and_deliverables value 2"
        )

    def test_patch_start_date(self):
        start_date = date.today().strftime("%Y-%m-%d")
        payload = {"start_date": start_date}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert str(self.barrier.id) == response.data["id"]
        assert start_date == response.data["start_date"]

    def test_patch_export_types(self):
        export_types_payload = ["goods", "services"]
        payload = {"export_types": export_types_payload}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert str(self.barrier.id) == response.data["id"]

        for response_type_item in response.data["export_types"]:
            assert response_type_item["name"] in export_types_payload

    def test_is_currently_active(self):
        """
        Barrier is active if it has a start date and it is in the past.
        """
        is_currently_active = "true"
        payload = {"is_currently_active": is_currently_active}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert str(self.barrier.id) == response.data["id"]
        assert is_currently_active


class TestHibernateEndpoint(APITestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory()
        self.url = reverse("hibernate-barrier", kwargs={"pk": self.barrier.id})

    @freezegun.freeze_time("2020-02-22")
    def test_hibernate_barrier_endpoint_sets_status_to_dormant(self):
        """
        Barrier status should be set to DORMANT when it gets hibernated.
        Also status date should be updated.
        """
        expected_status_date = "2020-02-22"
        dormant = 5
        assert 1 == self.barrier.status

        response = self.api_client.put(self.url)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert dormant == self.barrier.status
        assert expected_status_date == self.barrier.status_date.strftime("%Y-%m-%d")

    def test_update_barrier_through_hibernate_barrier_endpoint(self):
        """
        Users should be able to update status summary while hibernating a barrier.
        """
        status_summary = "some status summary"

        payload = {"status_summary": status_summary}
        response = self.api_client.put(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.barrier.refresh_from_db()
        assert status_summary == self.barrier.status_summary


class TestBarrierTradeDirection(APITestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory()
        self.url = reverse("get-barrier", kwargs={"pk": self.barrier.id})

    def test_get_barrier_without_trade_direction(self):
        """
        By default all existing barriers start with trade_direction not begin set.
        """
        self.barrier.trade_direction = None
        self.barrier.save()

        assert 1 == Barrier.objects.count()
        assert self.barrier.trade_direction is None

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert response.data["trade_direction"] is None

    def test_get_barrier_with_trade_direction(self):
        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["trade_direction"]["id"]

    def test_set_trade_direction_to_none(self):
        """
        Trade direction cannot be set to None.
        """
        payload = {"trade_direction": None}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_400_BAD_REQUEST == response.status_code
        assert 1 == self.barrier.trade_direction

    def test_patch_trade_direction(self):
        payload = {"trade_direction": 2}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["trade_direction"]["id"]

    def test_patch_trade_direction_with_invalid_values(self):
        invalid_values = [0, 14, "123", "Wibble", [], {"a": 6}, "null"]

        for value in invalid_values:
            with self.subTest(value=value):
                payload = {"trade_direction": value}
                response = self.api_client.patch(self.url, format="json", data=payload)

                assert (
                    status.HTTP_400_BAD_REQUEST == response.status_code
                ), f"Expected 400 when value is {value}"


class TestBarrierPublicEligibility(APITestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory()
        self.url = reverse("get-barrier", kwargs={"pk": self.barrier.id})

    def test_get_barrier_without_public_eligibility(self):
        """
        By default all existing barriers start with public_eligibility not begin set.
        """

        assert 1 == Barrier.objects.count()
        assert self.barrier.public_eligibility is None

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert response.data["public_eligibility"] is None

    def test_patch_public_eligibility_with_valid_values(self):
        valid_values = [True, False]

        for value in valid_values:
            with self.subTest(value=value):
                payload = {"public_eligibility": value}
                response = self.api_client.patch(self.url, format="json", data=payload)

                assert (
                    status.HTTP_200_OK == response.status_code
                ), f"Expected 200 when value is {value}"
                assert (
                    value == response.data["public_eligibility"]
                ), f'Expected {value} in "public_eligibility" field.'

    def test_patch_public_eligibility_with_invalid_values(self):
        invalid_values = [None, "", 123, {"1": "test"}, [1, 2, 3]]

        for value in invalid_values:
            with self.subTest(value=value):
                payload = {"public_eligibility": value}
                response = self.api_client.patch(self.url, format="json", data=payload)

                assert (
                    status.HTTP_400_BAD_REQUEST == response.status_code
                ), f"Expected 400 when value is {value}"

    def test_patch_public_eligibility_summary(self):
        summary = "Wibble wobble"
        payload = {"public_eligibility_summary": summary}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert (
            status.HTTP_200_OK == response.status_code
        ), f"Expected 200 when public_eligibility_summary is {summary}"
        assert summary == response.data["public_eligibility_summary"]

    def test_patch_public_eligibility_resets_public_eligibility_summary(self):
        self.barrier.public_eligibility = False
        self.barrier.public_eligibility_summary = "Wibble wobble"
        self.barrier.save()

        self.barrier.refresh_from_db()

        assert not self.barrier.public_eligibility
        assert self.barrier.public_eligibility_summary

        payload = {"public_eligibility": True}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert response.data["public_eligibility"]
        assert not response.data["public_eligibility_summary"]

    def test_patch_public_eligibility_with_permissions(self):
        pass

    def test_patch_public_eligibility_without_permissions(self):
        pass
