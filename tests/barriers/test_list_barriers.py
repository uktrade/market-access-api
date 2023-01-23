from unittest.mock import patch

import pytest
from django.contrib.postgres.search import SearchVector
from django.db.models import Q
from notifications_python_client.notifications import NotificationsAPIClient
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin, create_test_user
from api.history.models import CachedHistoryItem
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS, PublicBarrierStatus
from api.metadata.models import BarrierPriority, Organisation
from tests.action_plans.factories import (
    ActionPlanMilestoneFactory,
    ActionPlanStakeholderFactory,
    ActionPlanTaskFactory,
)
from tests.barriers.factories import BarrierFactory, ReportFactory
from tests.collaboration.factories import TeamMemberFactory
from tests.metadata.factories import CategoryFactory


# TODO: consider removing this test case.
class TestListBarriersBlankSystem(APITestMixin, APITestCase):
    """
    Found these in the old tests - they seem reluctant but keeping them just in case.
    """

    def test_no_barriers(self):
        """Test there are no reports using list"""
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_no_reports_counts(self):
        """Test there are no reports using list"""
        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 0
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["paused"] == 0
        assert response.data["barriers"]["resolved"] == 0
        assert response.data["reports"] == 0
        assert response.data["user"]["barriers"] == 0
        assert response.data["user"]["reports"] == 0


class TestListBarriers(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("list-barriers")

    def test_list_barriers_exclude_reports(self):
        """
        Draft barriers (reports) should be excluded.
        """
        _report = ReportFactory()
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

    def test_barrier_count_showing_count_for_all_and_user_report(self):
        """
        Users will see how many reports have been submitted and also how many they've submitted themselves.
        In this case 1 was submitted by the user.
        """
        ReportFactory()
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        ReportFactory(created_by=creator)
        client = self.create_api_client(user=creator)

        url = reverse("barrier-count")
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["barriers"]["total"]
        assert 0 == response.data["barriers"]["open"]
        assert 0 == response.data["barriers"]["resolved"]
        assert 2 == response.data["reports"]
        assert 0 == response.data["user"]["barriers"]
        assert 1 == response.data["user"]["reports"]

    def test_barrier_count_1_report_in_all_but_no_user_reports(self):
        """
        Users will see how many reports have been submitted and also how many they've submitted themselves.
        In this case 0 was submitted by the user.
        """
        ReportFactory()
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        client = self.create_api_client(user=creator)

        url = reverse("barrier-count")
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["barriers"]["total"]
        assert 0 == response.data["barriers"]["open"]
        assert 0 == response.data["barriers"]["resolved"]
        assert 1 == response.data["reports"]
        assert 0 == response.data["user"]["barriers"]
        assert 0 == response.data["user"]["reports"]

    def test_list_barriers_get_the_one_barrier(self):
        BarrierFactory()
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

    def test_include_archived_barriers(self):
        user = create_test_user()
        barrier = BarrierFactory()

        assert 1 == Barrier.objects.count()

        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

        barrier.archive(user=user)
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

    def test_list_barrier_without_archived_barriers(self):
        url = f"{self.url}?archived=0"
        user = create_test_user()
        barrier = BarrierFactory()

        assert 1 == Barrier.objects.count()

        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

        barrier.archive(user=user)
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

    def test_barrier_count_showing_count_for_all_and_user_barriers(self):
        """
        Users will see how many barriers have been created and also how many they've created themselves.
        In this case 1 was submitted by the user.
        """
        BarrierFactory(status=2)
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        BarrierFactory(created_by=creator)
        client = self.create_api_client(user=creator)

        url = reverse("barrier-count")
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["barriers"]["total"]
        assert 1 == response.data["barriers"]["open"]
        assert 0 == response.data["barriers"]["resolved"]
        assert 0 == response.data["reports"]
        assert 1 == response.data["user"]["barriers"]
        assert 0 == response.data["user"]["reports"]

    def test_barrier_count_1_barrier_in_all_but_no_user_barriers(self):
        """
        Users will see how many reports have been submitted and also how many they've submitted themselves.
        In this case 0 was submitted by the user.
        """
        BarrierFactory(status=2)
        BarrierFactory(status=4, status_summary="it wobbles!", status_date="2020-02-02")
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        client = self.create_api_client(user=creator)

        url = reverse("barrier-count")
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["barriers"]["total"]
        assert 1 == response.data["barriers"]["open"]
        assert 1 == response.data["barriers"]["resolved"]
        assert 0 == response.data["reports"]
        assert 0 == response.data["user"]["barriers"]
        assert 0 == response.data["user"]["reports"]

    def test_list_barriers_get_multiple_barriers(self):
        count = 2
        BarrierFactory.create_batch(count)

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert count == response.data["count"]

    def test_list_barriers_country_filter(self):
        country_id = "a05f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory.create_batch(2, country=country_id)
        BarrierFactory()

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?location={country_id}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = Barrier.objects.filter(country=country_id)
        assert barriers.count() == response.data["count"]

    def test_list_barriers_country_filter__multivalues(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        germany = "83756b9a-5d95-e211-a939-e4115bead28a"
        spain_barrier = BarrierFactory(country=spain)
        germany_barrier = BarrierFactory(country=germany)
        BarrierFactory()

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?location={spain},{germany}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(spain_barrier.id), str(germany_barrier.id)} == set(barrier_ids)

    def test_list_barriers_country_filter__no_find(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        germany = "83756b9a-5d95-e211-a939-e4115bead28a"
        BarrierFactory(country=spain)
        BarrierFactory()

        assert 2 == Barrier.objects.count()
        assert 0 == Barrier.objects.filter(country=germany).count()

        url = f'{reverse("list-barriers")}?location={germany}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 0 == response.data["count"]

    def test_list_barriers_status_filter(self):
        prob_status = 2
        BarrierFactory.create_batch(2, term=1)
        BarrierFactory(term=prob_status)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?status={prob_status}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = Barrier.objects.filter(status=prob_status)
        assert response.data["count"] == barriers.count()

    def test_list_barriers_status_filter__multivalues(self):
        BarrierFactory(term=1)
        BarrierFactory(term=2)
        BarrierFactory(term=4)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?status=2,4'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = Barrier.objects.filter(status__in=[2, 4])
        assert response.data["count"] == barriers.count()

    def test_list_barriers_category_filter(self):
        BarrierFactory()
        cat1 = CategoryFactory()
        barrier = BarrierFactory()
        barrier.categories.add(cat1)

        assert 2 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?category={cat1.id}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier.id) == response.data["results"][0]["id"]

    def test_list_barriers_sector_filter(self):
        sector1 = "75debee7-a182-410e-bde0-3098e4f7b822"
        sector2 = "af959812-6095-e211-a939-e4115bead28a"
        BarrierFactory(sectors=[sector1])
        barrier = BarrierFactory(sectors=[sector2])

        assert 2 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?sector={sector2}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier.id) == response.data["results"][0]["id"]

    def test_list_barriers_filter_location_europe(self):
        """
        Filter by overseas region - Europe
        Note (as of 2020 Apr) - not all countries are made available for tests
        """
        europe = "3e6809d6-89f6-4590-8458-1d0dab73ad1a"

        bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory(country=bhutan)
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        spain_barrier = BarrierFactory(country=spain)
        bahamas = "a25f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory(country=bahamas)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?location={europe}'
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(spain_barrier.id) == response.data["results"][0]["id"]

    def test_list_barriers_filter_location_multiple_regions(self):
        """
        Filter by overseas region - Europe & South Asia
        Note (as of 2020 Apr) - not all countries are made available for tests
        """
        europe = "3e6809d6-89f6-4590-8458-1d0dab73ad1a"
        south_asia = "12ed13cf-4b2c-4a46-b2f9-068e397d8c84"

        bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
        bhutan_barrier = BarrierFactory(country=bhutan)
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        spain_barrier = BarrierFactory(country=spain)
        bahamas = "a25f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory(country=bahamas)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?location={europe},{south_asia}'
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(bhutan_barrier.id), str(spain_barrier.id)} == set(barrier_ids)

    def test_list_barriers_overseas_region_trading_blocs(self):
        germany = "83756b9a-5d95-e211-a939-e4115bead28a"
        bahamas = "a25f66a0-5d95-e211-a939-e4115bead28a"
        europe = "3e6809d6-89f6-4590-8458-1d0dab73ad1a"

        eu_barrier = BarrierFactory(trading_bloc="TB00016")
        germany_barrier = BarrierFactory(country=germany)
        bahamas_barrier = BarrierFactory(country=bahamas)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?location={europe}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(eu_barrier.id), str(germany_barrier.id)} == set(barrier_ids)

    def test_list_barriers_text_filter_based_on_title(self):
        barrier1 = BarrierFactory(title="Wibble blockade")
        _barrier2 = BarrierFactory(title="Wobble blockade")
        barrier3 = BarrierFactory(title="Look wibble in the middle")

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?text=wibble'

        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier1.id), str(barrier3.id)} == set(barrier_ids)

    def test_list_barriers_text_filter_based_on_code(self):
        barrier1 = BarrierFactory(code="B-22-B30")
        barrier2 = BarrierFactory(code="B-22-SGM")

        assert 2 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?text=B-22-B30'

        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier1.id)} == set(barrier_ids)

    def test_list_barriers_text_filter_based_on_code_case_insensitive(self):
        barrier1 = BarrierFactory(code="B-22-B30")
        barrier2 = BarrierFactory(code="B-22-SGM")

        assert 2 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?text=b-22-b30'

        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier1.id)} == set(barrier_ids)

    def test_list_barriers_text_filter_based_on_summary(self):
        _barrier1 = BarrierFactory(summary="Wibble summary about the blockade.")
        barrier2 = BarrierFactory(summary="Wobble blockade")
        barrier3 = BarrierFactory(summary="Look ma, wibble-wobble in the middle.")

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?text=wobble'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier2.id), str(barrier3.id)} == set(barrier_ids)

    @pytest.mark.skip("""Failing on CircleCI for unknown reasons.""")
    def test_list_barriers_text_filter_based_on_public_id(self):
        barrier1 = BarrierFactory(public_barrier___title="Public Title")
        barrier2 = BarrierFactory(public_barrier___title="Public Title")
        barrier3 = BarrierFactory()

        public_id = f"PID-{barrier2.public_barrier.id}"

        assert 3 == Barrier.objects.count()

        from logging import getLogger

        logger = getLogger(__name__)

        search_queryset = Barrier.objects.annotate(
            search=SearchVector("summary"),
        ).filter(
            Q(code=public_id)
            | Q(search=public_id)
            | Q(title__icontains=public_id)
            | Q(public_barrier__id__iexact=public_id.lstrip("PID-").upper())
        )

        # assert 1 == search_queryset.count()
        search_queryset_count = search_queryset.count()
        logger.info(f"search_queryset_count: {search_queryset_count}")
        search_queryset_public_ids = [
            f"search_queryset: {barrier.title}: {barrier.public_barrier.id}"
            for barrier in search_queryset
        ]
        for public_id_string in search_queryset_public_ids:
            logger.info(public_id_string)

        public_ids = [
            f"Barrier.objects.all: {barrier.title}: {barrier.public_barrier.id}"
            for barrier in Barrier.objects.all()
        ]
        for public_id_string in public_ids:
            logger.info(public_id_string)

        url = f'{reverse("list-barriers")}?text={public_id}'
        logger.info(f"URL: {url}")
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        for name, value in response.data.items():
            logger.info(f"response.data {name}: {value}")

        assert 1 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier2.id)} == set(barrier_ids)

    def test_filter_barriers_my_barriers(self):
        BarrierFactory()
        _user1 = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        _barrier1 = BarrierFactory()
        user2 = create_test_user(sso_user_id=self.sso_creator["user_id"])
        barrier2 = BarrierFactory(created_by=user2)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?user={user2.id}'
        client = self.create_api_client(user=user2)
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier2.id) == response.data["results"][0]["id"]

    def test_trade_direction_filter(self):
        barrier1 = BarrierFactory()
        barrier1.trade_direction = None
        barrier1.save()
        barrier2 = BarrierFactory(trade_direction=1)
        barrier3 = BarrierFactory(trade_direction=2)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?trade_direction=1,2'

        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier2.id), str(barrier3.id)} == set(barrier_ids)

    def test_wto_has_been_notified_filter(self):
        barrier1 = BarrierFactory(wto_profile__wto_has_been_notified=True)
        barrier2 = BarrierFactory(wto_profile__wto_has_been_notified=False)
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=wto_has_been_notified'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_wto_should_be_notified_filter(self):
        barrier1 = BarrierFactory(wto_profile__wto_should_be_notified=True)
        barrier2 = BarrierFactory(wto_profile__wto_should_be_notified=False)
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=wto_should_be_notified'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_has_wto_raised_date_filter(self):
        barrier1 = BarrierFactory(wto_profile__raised_date="2020-01-31")
        barrier2 = BarrierFactory(wto_profile__raised_date=None)
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=has_raised_date'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_has_wto_committee_raised_in_filter(self):
        barrier1 = BarrierFactory(wto_profile__committee_raised_in__name="Committee X")
        barrier2 = BarrierFactory(wto_profile__committee_raised_in=None)
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=has_committee_raised_in'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_has_wto_case_number_filter(self):
        barrier1 = BarrierFactory(wto_profile__case_number="CASE123")
        barrier2 = BarrierFactory(wto_profile__case_number="")
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=has_case_number'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_has_no_information_filter(self):
        barrier1 = BarrierFactory(wto_profile__case_number="CASE123")
        barrier2 = BarrierFactory(wto_profile__wto_should_be_notified=True)
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=has_no_information'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        barrier_ids = [result["id"] for result in response.data["results"]]
        assert str(barrier1.id) not in barrier_ids
        assert str(barrier2.id) not in barrier_ids
        assert str(barrier3.id) in barrier_ids

    def test_wto_filters_or_together(self):
        barrier1 = BarrierFactory(wto_profile__case_number="CASE123")
        barrier2 = BarrierFactory(wto_profile__raised_date="2020-01-31")
        barrier3 = BarrierFactory(wto_profile=None)

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?wto=has_case_number,has_raised_date'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [result["id"] for result in response.data["results"]]
        assert str(barrier1.id) in barrier_ids
        assert str(barrier2.id) in barrier_ids
        assert str(barrier3.id) not in barrier_ids

    def test_member_filter(self):
        user1 = create_test_user()
        _barrier0 = BarrierFactory()
        barrier1 = BarrierFactory(created_by=user1)
        member1 = TeamMemberFactory(
            barrier=barrier1, user=user1, role="Reporter", default=True
        )
        barrier2 = BarrierFactory(created_by=user1)
        TeamMemberFactory(barrier=barrier2, user=user1, role="Contributor")

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?member={member1.id}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier1.id), str(barrier2.id)} == set(barrier_ids)

    def test_member_filter__distinct_records(self):
        """
        Only include the barrier once even if the user is listed multiple times as a member for a barrier.
        """
        user1 = create_test_user()
        barrier1 = BarrierFactory(created_by=user1)
        member1 = TeamMemberFactory(
            barrier=barrier1, user=user1, role="Reporter", default=True
        )
        member2 = TeamMemberFactory(
            barrier=barrier1, user=user1, role="Owner", default=True
        )

        assert 1 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?member={member1.id}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

    def test_organisation_filter(self):
        org1 = Organisation.objects.get(id=1)
        barrier1 = BarrierFactory()
        barrier1.organisations.add(org1)
        barrier2 = BarrierFactory()

        assert 2 == Barrier.objects.count()
        assert 1 == Barrier.objects.filter(organisations__in=[org1]).count()

        url = f'{reverse("list-barriers")}?organisation={org1.id}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_organisation_filter__distinct_records(self):
        org1 = Organisation.objects.get(id=1)
        org2 = Organisation.objects.get(id=2)
        barrier1 = BarrierFactory()
        barrier1.organisations.add(org1, org2)
        barrier2 = BarrierFactory()

        assert 2 == Barrier.objects.count()
        assert 1 == Barrier.objects.filter(organisations__in=[org1]).count()

        url = (
            f'{reverse("list-barriers")}?organisation={org1.id}&?organisation={org2.id}'
        )
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier1.id) == response.data["results"][0]["id"]

    def test_dataset_barrier_list_returns_without_error(self):
        BarrierFactory(status=1, status_summary="it wobbles!", status_date="2020-02-02")
        BarrierFactory(status=2, status_summary="it wobbles!", status_date="2020-02-02")
        BarrierFactory(status=3, status_summary="it wobbles!", status_date="2020-02-02")
        BarrierFactory(status=4, status_summary="it wobbles!", status_date="2020-02-02")
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        client = self.create_api_client(user=creator)

        url = reverse("dataset:barrier-list")
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 4 == len(response.data["results"])
        assert response.data["next"] is None
        assert response.data["previous"] is None

    def test_barrier_status_date_filter_no_results(self):
        BarrierFactory(status=4, status_date="2025-02-02")

        url = f'{reverse("list-barriers")}?status=4&status_date_resolved_in_full=2021-01-01,2021-06-30'

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        barrier_ids = []
        for result in response.data["results"]:
            barrier_ids.append(result["id"])

        assert barrier_ids == []

    def test_barrier_status_date_filter_open_pending_action(self):
        barrier = BarrierFactory(status=1, estimated_resolution_date="2020-06-06")

        url = f'{reverse("list-barriers")}?status=1&status_date_open_pending_action=2020-01-01,2021-06-30'

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        barrier_ids = []
        for result in response.data["results"]:
            barrier_ids.append(result["id"])

        assert barrier_ids == [str(barrier.id)]

    def test_barrier_status_date_filter_open_in_progress(self):
        barrier = BarrierFactory(status=2, estimated_resolution_date="2020-06-06")

        url = f'{reverse("list-barriers")}?status=2&status_date_open_in_progress=2020-01-01,2021-06-30'

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        barrier_ids = []
        for result in response.data["results"]:
            barrier_ids.append(result["id"])

        assert barrier_ids == [str(barrier.id)]

    def test_barrier_status_date_filter_resolved_in_part(self):
        barrier = BarrierFactory(status=3, status_date="2020-02-02")

        url = f'{reverse("list-barriers")}?status=3&status_date_resolved_in_part=2020-01-01,2021-06-30'

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        barrier_ids = []
        for result in response.data["results"]:
            barrier_ids.append(result["id"])

        assert barrier_ids == [str(barrier.id)]

    def test_barrier_status_date_filter_resolved_in_full(self):
        barrier = BarrierFactory(status=4, status_date="2020-02-02")

        url = f'{reverse("list-barriers")}?status=4&status_date_resolved_in_full=2020-01-01,2021-06-30'

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        barrier_ids = []
        for result in response.data["results"]:
            barrier_ids.append(result["id"])

        assert barrier_ids == [str(barrier.id)]

    def test_barrier_status_date_filter_multiple_status(self):
        barrier_open_pending = BarrierFactory(
            status=1, estimated_resolution_date="2020-06-06"
        )
        barrier_open_in_progress = BarrierFactory(
            status=2, estimated_resolution_date="2020-06-06"
        )
        barrier_resolved_in_part = BarrierFactory(status=3, status_date="2020-02-02")
        barrier_resolved_in_full = BarrierFactory(status=4, status_date="2020-02-02")

        saved_barrier_list = [
            str(barrier_resolved_in_full.id),
            str(barrier_resolved_in_part.id),
            str(barrier_open_in_progress.id),
            str(barrier_open_pending.id),
        ]

        url = (
            f'{reverse("list-barriers")}?'
            "status=1,2,3,4&"
            "status_date_open_pending_action=2020-01-01,2021-06-30&"
            "status_date_open_in_progress=2020-01-01,2021-06-30&"
            "status_date_resolved_in_part=2020-01-01,2021-06-30&"
            "status_date_resolved_in_full=2020-01-01,2021-06-30&"
        )

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        barrier_ids = []
        for result in response.data["results"]:
            barrier_ids.append(result["id"])

        assert barrier_ids == saved_barrier_list

    def test_has_value_for_is_top_priority(self):
        BarrierFactory()
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        serialised_data = response.data
        assert "is_top_priority" in serialised_data["results"][0].keys()

    def test_value_for_is_top_priority_is_bool(self):
        BarrierFactory()
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        serialised_data = response.data
        assert "is_top_priority" in serialised_data["results"][0].keys() and isinstance(
            serialised_data["results"][0]["is_top_priority"], bool
        )

    def test_is_top_priority_barrier(self):

        # Left: top_priority_status - Right: expected is_top_priority value
        top_priority_status_to_is_top_priority_map = {
            TOP_PRIORITY_BARRIER_STATUS.APPROVED: True,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING: True,
            TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING: False,
            TOP_PRIORITY_BARRIER_STATUS.NONE: False,
        }

        barrier = BarrierFactory()
        test_user = create_test_user()
        TeamMemberFactory(barrier=barrier, user=test_user, role="Owner", default=True)

        for (
            top_priority_status,
            is_top_priority,
        ) in top_priority_status_to_is_top_priority_map.items():

            with patch.object(
                NotificationsAPIClient, "send_email_notification", return_value=None
            ) as mock:
                barrier.top_priority_status = top_priority_status
                barrier.save()

            response = self.api_client.get(self.url)
            assert status.HTTP_200_OK == response.status_code
            serialised_data = response.data

            # make sure the same barrier is compared
            assert serialised_data["results"][0]["id"] == str(barrier.id)
            assert "is_top_priority" in serialised_data["results"][0].keys()
            assert serialised_data["results"][0]["is_top_priority"] == is_top_priority
            assert (
                serialised_data["results"][0]["top_priority_status"]
                == top_priority_status
            )

    def test_top_priority_search_returns_removal_pending(self):
        approved_barrier = BarrierFactory()
        approved_barrier.top_priority_status = "APPROVED"
        approved_barrier.save()

        removal_pending_barrier = BarrierFactory()
        removal_pending_barrier.top_priority_status = "REMOVAL_PENDING"
        removal_pending_barrier.save()

        approved_url = f'{reverse("list-barriers")}?top_priority_status=APPROVED'
        approved_response = self.api_client.get(approved_url)
        assert approved_response.status_code == status.HTTP_200_OK
        approved_serialised_data = approved_response.data
        assert len(approved_serialised_data["results"]) == 2

        removal_pending_url = (
            f'{reverse("list-barriers")}?top_priority_status=REMOVAL_PENDING'
        )
        removal_pending_response = self.api_client.get(removal_pending_url)
        assert removal_pending_response.status_code == status.HTTP_200_OK
        removal_pending_serialised_data = removal_pending_response.data
        assert len(removal_pending_serialised_data["results"]) == 1


class PublicViewFilterTest(APITestMixin, APITestCase):
    def test_changed_filter(self):
        url = f'{reverse("list-barriers")}?public_view=changed'
        barrier1 = BarrierFactory(
            public_barrier___public_view_status=PublicBarrierStatus.PUBLISHED,
            public_barrier__last_published_on="2020-08-01",
            priority="LOW",
            source="COMPANY",
        )
        barrier2 = BarrierFactory(
            public_barrier___public_view_status=PublicBarrierStatus.PUBLISHED,
            public_barrier__last_published_on="2020-08-01",
        )
        barrier3 = BarrierFactory(
            public_barrier___public_view_status=PublicBarrierStatus.PUBLISHED,
            public_barrier__last_published_on="2020-08-01",
        )
        CachedHistoryItem.objects.all().delete()

        # No barriers should have 'changed' since being published
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

        # Change some fields that do not affect the public barrier
        barrier1.source = "TRADE"
        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        # No barriers should have 'changed' since being published
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

        # Change a field that does affect the public barrier
        barrier1.summary = "New summary"
        barrier1.save()

        # barrier1 should now be in the search results for changed barriers
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        barrier_ids = set([result["id"] for result in response.data["results"]])
        assert set([str(barrier1.id)]) == barrier_ids

        # Change a field that does affect the public barrier
        barrier2.sectors = ["9f38cecc-5f95-e211-a939-e4115bead28a"]
        barrier2.save()

        # barrier2 should now also be in the search results for changed barriers
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = set([result["id"] for result in response.data["results"]])
        assert set([str(barrier1.id), str(barrier2.id)]) == barrier_ids

    def test_location_filter(self):
        base_url = reverse("list-barriers")

        # European Union
        barrier1 = BarrierFactory(trading_bloc="TB00016")
        # France
        barrier2 = BarrierFactory(
            country="82756b9a-5d95-e211-a939-e4115bead28a",
            caused_by_trading_bloc=True,
        )
        # France
        barrier3 = BarrierFactory(
            country="82756b9a-5d95-e211-a939-e4115bead28a",
            caused_by_trading_bloc=False,
        )
        # Brazil
        barrier4 = BarrierFactory(
            country="b05f66a0-5d95-e211-a939-e4115bead28a",
        )

        # Search by trading bloc
        response = self.api_client.get(f"{base_url}?location=TB00016")
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        barrier_ids = set([result["id"] for result in response.data["results"]])
        assert set([str(barrier1.id)]) == barrier_ids

        # Search by trading_bloc or country
        response = self.api_client.get(
            f"{base_url}?location=82756b9a-5d95-e211-a939-e4115bead28a,TB00016"
        )
        assert status.HTTP_200_OK == response.status_code
        assert 3 == response.data["count"]
        barrier_ids = set([result["id"] for result in response.data["results"]])
        assert (
            set([str(barrier1.id), str(barrier2.id), str(barrier3.id)]) == barrier_ids
        )

        # Search by trading_bloc, including country specific barriers
        response = self.api_client.get(
            f"{base_url}?location=TB00016&country_trading_bloc=TB00016"
        )
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = set([result["id"] for result in response.data["results"]])
        assert set([str(barrier1.id), str(barrier2.id)]) == barrier_ids

    def test_action_plan_filter(self):
        base_url = reverse("list-barriers")
        barriers = BarrierFactory.create_batch(3)

        action_plan = barriers[0].action_plan
        action_plan.current_status = "NOT_STARTED"
        action_plan.save()
        response = self.api_client.get(f"{base_url}?has_action_plan=1")
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

        milestones = ActionPlanMilestoneFactory.create_batch(3, action_plan=action_plan)

        response = self.api_client.get(f"{base_url}?has_action_plan=1")
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

        tasks = ActionPlanTaskFactory.create_batch(3, milestone=milestones[0])
        tasks2 = ActionPlanTaskFactory.create_batch(3, milestone=milestones[1])

        response = self.api_client.get(f"{base_url}?has_action_plan=1")
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

        action_plan2 = barriers[1].action_plan
        milestones2 = ActionPlanMilestoneFactory.create_batch(
            3, action_plan=action_plan2
        )

        response = self.api_client.get(f"{base_url}?has_action_plan=1")
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]

        stakeholders = ActionPlanStakeholderFactory.create_batch(
            3, action_plan=action_plan
        )
        response = self.api_client.get(f"{base_url}?has_action_plan=1")
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
