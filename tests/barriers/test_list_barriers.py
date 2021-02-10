from datetime import datetime

from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import Barrier
from api.history.models import CachedHistoryItem
from api.metadata.constants import PublicBarrierStatus
from api.metadata.models import BarrierPriority, Organisation
from tests.barriers.factories import BarrierFactory, ReportFactory
from tests.collaboration.factories import TeamMemberFactory
from tests.metadata.factories import CategoryFactory, BarrierPriorityFactory


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

    def test_list_barriers_order_by(self):
        test_parameters = [
            "reported_on",
            "-reported_on",
            "modified_on",
            "-modified_on",
            "status",
            "-status",
            "priority",
            "-priority",
            "country",
            "-country",
        ]
        priorities = BarrierPriorityFactory.create_batch(3)
        bahamas = "a25f66a0-5d95-e211-a939-e4115bead28a"
        barrier1 = BarrierFactory(
            reported_on=datetime(2020, 1, 1, tzinfo=UTC),
            modified_on=datetime(2020, 1, 2, tzinfo=UTC),
            status=1,
            priority=priorities[0],
            country=bahamas,
        )
        bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
        barrier2 = BarrierFactory(
            reported_on=datetime(2020, 2, 2, tzinfo=UTC),
            modified_on=datetime(2020, 2, 3, tzinfo=UTC),
            status=2,
            priority=priorities[1],
            country=bhutan,
        )
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        barrier3 = BarrierFactory(
            reported_on=datetime(2020, 3, 3, tzinfo=UTC),
            modified_on=datetime(2020, 3, 4, tzinfo=UTC),
            status=7,
            priority=priorities[2],
            country=spain,
        )

        assert 3 == Barrier.objects.count()

        for order_by in test_parameters:
            with self.subTest(order_by=order_by):
                url = f'{reverse("list-barriers")}?ordering={order_by}'
                response = self.api_client.get(url)

                assert response.status_code == status.HTTP_200_OK
                barriers = Barrier.objects.all().order_by(order_by)
                assert barriers.count() == response.data["count"]
                response_list = [b["id"] for b in response.data["results"]]
                db_list = [str(b.id) for b in barriers]
                assert db_list == response_list

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

    def test_list_barriers_text_filter_based_on_public_id(self):
        barrier1 = BarrierFactory(public_barrier___title="Public Title")
        barrier2 = BarrierFactory(public_barrier___title="Public Title")
        barrier3 = BarrierFactory()

        public_id = f"PID-{barrier2.public_barrier.id}"

        assert 3 == Barrier.objects.count()

        url = f'{reverse("list-barriers")}?text={public_id}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
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
