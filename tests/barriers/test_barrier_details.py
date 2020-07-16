from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse

from freezegun import freeze_time
from rest_framework.test import APITestCase

from api.barriers.helpers import get_team_members
from api.barriers.models import BarrierInstance, PublicBarrier
from api.barriers.serializers import PublicBarrierSerializer
from api.metadata.constants import PublicBarrierStatus, BarrierStatus
from api.metadata.models import Category, BarrierPriority
from api.core.test_utils import APITestMixin
from api.metadata.utils import get_country
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import CategoryFactory


class TestBarrierDetails(APITestMixin, APITestCase):

    def setUp(self):
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
        assert status_date == self.barrier.status_date.strftime('%Y-%m-%d')
        assert status_summary == self.barrier.status_summary

    @freeze_time("2020-02-22")
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
        assert "2020-02-22" == self.barrier.status_date.strftime('%Y-%m-%d')
        assert status_summary == self.barrier.status_summary

    @freeze_time("2020-02-22")
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
        assert "2020-02-22" == self.barrier.status_date.strftime('%Y-%m-%d')
        assert status_summary == self.barrier.status_summary

    def test_patch_barrier_title(self):
        title = "Just a new title"
        payload = {
            "barrier_title": title
        }
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert title == response.data["barrier_title"]

    def test_patch_barrier_problem_status(self):
        assert 1 == self.barrier.problem_status

        test_parameters = [
            {"problem_status": None, "status_code": status.HTTP_200_OK, "expected_problem_status": None},
            {"problem_status": 2, "status_code": status.HTTP_200_OK, "expected_problem_status": 2},
            {"problem_status": 1, "status_code": status.HTTP_200_OK, "expected_problem_status": 1},
            {"problem_status": 0, "status_code": status.HTTP_400_BAD_REQUEST, "expected_problem_status": 1},
            {"problem_status": "ahoy!", "status_code": status.HTTP_400_BAD_REQUEST, "expected_problem_status": 1},
            {"problem_status": "987", "status_code": status.HTTP_400_BAD_REQUEST, "expected_problem_status": 1},
        ]

        for tp in test_parameters:
            with self.subTest(tp=tp):
                payload = {"problem_status": tp["problem_status"],}
                response = self.api_client.patch(self.url, format="json", data=payload)

                self.barrier.refresh_from_db()
                assert tp["status_code"] == response.status_code, f"Test params: {tp}"
                assert tp["expected_problem_status"] == self.barrier.problem_status, f"Test params: {tp}"

    def test_patch_barrier_to_affect_all_sectors(self):
        assert not self.barrier.all_sectors
        assert 1 == len(self.barrier.sectors)

        payload = {"all_sectors": True}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert str(self.barrier.id) == response.data["id"]
        assert response.data["all_sectors"] is True
        assert self.barrier.sectors == response.data["sectors"]

    def test_patch_barrier_priority(self):
        unknown_priority = BarrierPriority.objects.get(code="UNKNOWN")
        assert unknown_priority == self.barrier.priority

        priorities = ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]

        for priority in priorities:
            with self.subTest(priority=priority):
                payload = {
                    "priority": priority,
                    "priority_summary": "wibble wobble"
                }

                response = self.api_client.patch(self.url, format="json", data=payload)

                assert status.HTTP_200_OK == response.status_code
                assert str(self.barrier.id) == response.data["id"]
                assert priority == response.data["priority"]["code"]

    def test_add_barrier_categories(self):
        categories = Category.objects.all()
        category1 = categories[0]
        category2 = categories[1]
        self.barrier.categories.add(category1)

        self.barrier.refresh_from_db()
        assert 1 == self.barrier.categories.count()

        payload = {
            "categories": (category1.id, category2.id)
        }
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert {category1.id, category2.id} == set(response.data["categories"])

    def test_replace_barrier_categories(self):
        categories = Category.objects.all()
        category1 = categories[0]
        category2 = categories[1]
        category3 = categories[2]
        self.barrier.categories.add(category1)

        self.barrier.refresh_from_db()
        assert 1 == self.barrier.categories.count()

        payload = {
            "categories": (category2.id, category3.id)
        }
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert {category2.id, category3.id} == set(response.data["categories"])

    def test_flush_barrier_categories(self):
        categories = Category.objects.all()
        category1 = categories[0]
        self.barrier.categories.add(category1)

        self.barrier.refresh_from_db()
        assert 1 == self.barrier.categories.count()

        payload = {
            "categories": ()
        }
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert not response.data["categories"]

    def test_update_barrier_adds_user_as_contributor(self):
        """ Users who edit a barrier should be  added as a Contributor automatically. """
        assert not get_team_members(self.barrier)

        payload = {"barrier_title": "Wibble wobble"}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        team_members = get_team_members(self.barrier)
        assert 1 == team_members.count()
        assert "Contributor" == team_members.first().role


class TestHibernateEndpoint(APITestMixin, TestCase):

    def setUp(self):
        self.barrier = BarrierFactory()
        self.url = reverse("hibernate-barrier", kwargs={"pk": self.barrier.id})

    @freeze_time("2020-02-22")
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
        assert expected_status_date == self.barrier.status_date.strftime('%Y-%m-%d')

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
        self.barrier = BarrierFactory()
        self.url = reverse("get-barrier", kwargs={"pk": self.barrier.id})

    def test_get_barrier_without_trade_direction(self):
        """
        By default all existing barriers start with trade_direction not begin set.
        """
        self.barrier.trade_direction = None
        self.barrier.save()

        assert 1 == BarrierInstance.objects.count()
        assert self.barrier.trade_direction is None

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert response.data["trade_direction"] is None

    def test_get_barrier_with_trade_direction(self):
        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["trade_direction"]

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
        assert 2 == response.data["trade_direction"]

    def test_patch_trade_direction_with_invalid_values(self):
        invalid_values = [0, 14, "123", "Wibble", [], {"a": 6}, "null"]

        for value in invalid_values:
            with self.subTest(value=value):
                payload = {"trade_direction": value}
                response = self.api_client.patch(self.url, format="json", data=payload)

                assert status.HTTP_400_BAD_REQUEST == response.status_code, \
                    f"Expected 400 when value is {value}"


class TestBarrierPublicEligibility(APITestMixin, TestCase):
    def setUp(self):
        self.barrier = BarrierFactory()
        self.url = reverse("get-barrier", kwargs={"pk": self.barrier.id})

    def test_get_barrier_without_public_eligibility(self):
        """
        By default all existing barriers start with public_eligibility not begin set.
        """

        assert 1 == BarrierInstance.objects.count()
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

                assert status.HTTP_200_OK == response.status_code, \
                    f"Expected 200 when value is {value}"
                assert value == response.data["public_eligibility"], \
                    f'Expected {value} in "public_eligibility" field.'

    def test_patch_public_eligibility_with_invalid_values(self):
        invalid_values = [None, "", 123, {"1": "test"}, [1, 2, 3]]

        for value in invalid_values:
            with self.subTest(value=value):
                payload = {"public_eligibility": value}
                response = self.api_client.patch(self.url, format="json", data=payload)

                assert status.HTTP_400_BAD_REQUEST == response.status_code, \
                    f"Expected 400 when value is {value}"

    def test_patch_public_eligibility_summary(self):
        summary = "Wibble wobble"
        payload = {"public_eligibility_summary": summary}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code, \
            f"Expected 200 when public_eligibility_summary is {summary}"
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


class TestPublicBarrier(APITestMixin, TestCase):
    def setUp(self):
        self.barrier = BarrierFactory()
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def test_public_barrier_gets_created_at_fetch(self):
        """
        If a barrier doesn't have a corresponding public barrier it gets created when
        details of that being fetched.
        """
        assert 1 == BarrierInstance.objects.count()
        assert 0 == PublicBarrier.objects.count()

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code

        assert 1 == BarrierInstance.objects.count()
        assert 1 == PublicBarrier.objects.count()

    def test_public_barrier_default_values_at_creation(self):
        """
        Defaults should be set when the public barrier gets created.
        """
        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert not response.data["title"]
        assert not response.data["summary"]
        assert self.barrier.export_country == response.data["country"]
        assert self.barrier.sectors == response.data["sectors"]
        assert not response.data["categories"]

    def test_public_barrier_default_categories_at_creation(self):
        """
        Check that all categories are being set for the public barrier.
        """
        categories_count = 3
        categories = CategoryFactory.create_batch(categories_count)
        expected_categories = [c.title for c in categories]
        self.barrier.categories.add(*categories)

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert categories_count == len(response.data["categories"])
        assert set(expected_categories) == set(response.data["categories"])

    # === PATCH ===
    def test_public_barrier_patch_as_regular_user(self):
        """ Regular users cannot patch public barriers """
        pass

    def test_public_barrier_patch_as_sifter(self):
        """ Sifters cannot patch public barriers """
        pass

    def test_public_barrier_patch_as_editor(self):
        """ Editors can patch public barriers """
        pass

    @freeze_time("2020-02-02")
    def test_public_barrier_patch_as_publisher(self):
        """ Publishers can patch public barriers """
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_title == response.data["title"]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]
        assert not response.data["summary"]
        assert not response.data["summary_updated_on"]

    @freeze_time("2020-02-02")
    def test_public_barrier_patch_summary_as_publisher(self):
        """ Publishers can patch public barriers """
        public_summary = "New public facing summary!"
        payload = {"summary": public_summary}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_summary == response.data["summary"]
        assert "2020-02-02" == response.data["summary_updated_on"].split("T")[0]
        assert not response.data["title"]
        assert not response.data["title_updated_on"]

    # === READY ====
    def test_public_barrier_marked_ready_as_editor(self):
        """ Editors can mark public barriers unprepared (not ready) """
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.READY == response.data["public_view_status"]

    # === UNPREPARED ====
    def test_public_barrier_marked_unprepared_as_editor(self):
        """ Editors can mark a public barriers unprepared (not ready) """
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.ELIGIBLE == response.data["public_view_status"]

    # === IGNORE ALL CHANGES ====
    @freeze_time("2020-02-02")
    def test_public_barrier_ignore_all_changes_as_publisher(self):
        """ Publishers can ignore all changes """
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert "2020-02-02" == response.data["summary_updated_on"].split("T")[0]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]

    # === PUBLISH ====
    def test_public_barrier_publish_as_regular_user(self):
        """ Regular users cannot publish public barriers """
        pass

    def test_public_barrier_publish_as_sifter(self):
        """ Sifters cannot publish public barriers """
        pass

    def test_public_barrier_publish_as_editor(self):
        """ Editors cannot publish public barriers """
        pass

    def test_public_barrier_publish_as_publisher(self):
        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.PUBLISHED == response.data["public_view_status"]
        assert response.data["first_published_on"]
        assert response.data["last_published_on"]
        assert not response.data["unpublished_on"]

    def test_public_barrier_publish_creates_a_published_version(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert not pb.published_versions
        assert not pb.latest_published_version

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        _response = self.api_client.post(url)

        pb.refresh_from_db()
        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_new_published_version(self):
        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        pb = PublicBarrier.objects.get(pk=response.data["id"])
        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

        response = self.api_client.post(url)

        pb.refresh_from_db()
        assert 2 == len(pb.published_versions["versions"])
        assert '2' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_latest_published_version_attributes(self):
        self.barrier.sectors = ['9b38cecc-5f95-e211-a939-e4115bead28a']
        expected_sectors = [{"name": "Chemicals"}]
        category = CategoryFactory()
        self.barrier.categories.add(category)
        expected_categories = [{"name": category.title}]
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.title = "Title 1"
        pb.summary = "Summary 1"
        pb.save()

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert "Title 1" == response.data["latest_published_version"]["title"]
        assert "Summary 1" == response.data["latest_published_version"]["summary"]
        assert BarrierStatus.name(self.barrier.status) == response.data["latest_published_version"]["status"]
        assert get_country(self.barrier.export_country) == response.data["latest_published_version"]["country"]
        assert expected_sectors == response.data["latest_published_version"]["sectors"]
        assert response.data["latest_published_version"]["all_sectors"] is False
        assert expected_categories == response.data["latest_published_version"]["categories"]

    def test_public_barrier_latest_published_version_not_affected_by_updates(self):
        self.barrier.sectors = ['9b38cecc-5f95-e211-a939-e4115bead28a']
        expected_sectors = [{"name": "Chemicals"}]
        category = CategoryFactory()
        self.barrier.categories.add(category)
        expected_categories = [{"name": category.title}]
        expected_status = BarrierStatus.name(BarrierStatus.OPEN_PENDING)
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.title = "Title 1"
        pb.summary = "Summary 1"
        pb.save()

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)
        pb.refresh_from_db()

        # Let's do some mods to self.barrier and public barrier
        self.barrier.status = BarrierStatus.OPEN_IN_PROGRESS
        self.barrier.summary = "Updated internal barrier summary"
        self.barrier.sectors = ["9538cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.save()
        pb.title = "Title 2"
        pb.save()

        # There should be no new published versions, and the previous published version should keep its state
        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert "Title 1" == response.data["latest_published_version"]["title"]
        assert "Summary 1" == response.data["latest_published_version"]["summary"]
        assert expected_status == response.data["latest_published_version"]["status"]
        assert get_country(self.barrier.export_country) == response.data["latest_published_version"]["country"]
        assert expected_sectors == response.data["latest_published_version"]["sectors"]
        assert response.data["latest_published_version"]["all_sectors"] is False
        assert expected_categories == response.data["latest_published_version"]["categories"]

    def test_public_barrier_publish_updates_non_editable_fields(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert not pb.categories.all()

        # self.barrier.sectors = ['9b38cecc-5f95-e211-a939-e4115bead28a']
        category = CategoryFactory()
        self.barrier.categories.add(category)
        self.barrier.save()

        # expected_categories = [{"name": category.title}]
        # expected_sectors = [{"name": "Chemicals"}]
        # expected_status = BarrierStatus.name(BarrierStatus.OPEN_PENDING)

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        pb.refresh_from_db()
        assert pb.categories.first()
        assert category.id == pb.categories.first().id
        # assert '1' == pb.published_versions["latest_version"]
        # assert pb.latest_published_version

        # response = self.api_client.post(url)

        # pb.refresh_from_db()
        # assert 2 == len(pb.published_versions["versions"])
        # assert '2' == pb.published_versions["latest_version"]
        # assert pb.latest_published_version

    # === UNPUBLISH ===
    # TODO: wrap this up

    def test_public_barrier_unpublish_as_publisher(self):
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.UNPUBLISHED == response.data["public_view_status"]
        assert response.data["unpublished_on"]

    def test_update_eligibility_on_attr_access(self):
        test_parameters = [
            {
                "case_id": 10,
                "public_eligibility": None,
                "public_view_status": PublicBarrierStatus.UNKNOWN,
                "expected_public_view_status": PublicBarrierStatus.UNKNOWN
            },
            {
                "case_id": 20,
                "public_eligibility": True,
                "public_view_status": PublicBarrierStatus.UNKNOWN,
                "expected_public_view_status": PublicBarrierStatus.ELIGIBLE
            },
            {
                "case_id": 30,
                "public_eligibility": False,
                "public_view_status": PublicBarrierStatus.UNKNOWN,
                "expected_public_view_status": PublicBarrierStatus.INELIGIBLE
            },
            {
                "case_id": 40,
                "public_eligibility": False,
                "public_view_status": PublicBarrierStatus.ELIGIBLE,
                "expected_public_view_status": PublicBarrierStatus.INELIGIBLE
            },
            {
                "case_id": 50,
                "public_eligibility": True,
                "public_view_status": PublicBarrierStatus.INELIGIBLE,
                "expected_public_view_status": PublicBarrierStatus.ELIGIBLE
            },
            {
                "case_id": 60,
                "public_eligibility": True,
                "public_view_status": PublicBarrierStatus.READY,
                "expected_public_view_status": PublicBarrierStatus.READY
            },
            {
                "case_id": 70,
                "public_eligibility": False,
                "public_view_status": PublicBarrierStatus.READY,
                "expected_public_view_status": PublicBarrierStatus.INELIGIBLE
            },
            # Published state is protected and cannot change without unpublishing first
            {
                "case_id": 80,
                "public_eligibility": True,
                "public_view_status": PublicBarrierStatus.PUBLISHED,
                "expected_public_view_status": PublicBarrierStatus.PUBLISHED
            },
            {
                "case_id": 90,
                "public_eligibility": False,
                "public_view_status": PublicBarrierStatus.PUBLISHED,
                "expected_public_view_status": PublicBarrierStatus.PUBLISHED
            },
            {
                "case_id": 100,
                "public_eligibility": False,
                "public_view_status": PublicBarrierStatus.UNPUBLISHED,
                "expected_public_view_status": PublicBarrierStatus.INELIGIBLE
            },
        ]

        for params in test_parameters:
            with self.subTest(params=params):
                barrier = BarrierFactory()
                url = reverse("public-barriers-detail", kwargs={"pk": barrier.id})
                payload = {
                    "public_view_status": params["public_view_status"],
                }
                response = self.api_client.get(url)
                public_barrier = PublicBarrier.objects.get(pk=response.data["id"])
                public_barrier.public_view_status = params["public_view_status"]
                public_barrier.save()

                # Now check that changing the public eligibility on the internal barrier
                # affects the public barrier status the way it's expected
                barrier.public_eligibility = params["public_eligibility"]
                barrier.save()

                response = self.api_client.get(url)

                assert params["expected_public_view_status"] == response.data["public_view_status"], \
                    f"Failed at Case {params['case_id']}"


class TestPublicBarrierSerializer(APITestMixin, TestCase):

    def setUp(self):
        self.barrier = BarrierFactory(
            export_country="1f0be5c4-5d95-e211-a939-e4115bead28a",  # Singapore
            sectors=['9b38cecc-5f95-e211-a939-e4115bead28a'],       # Chemicals
            status=BarrierStatus.OPEN_PENDING
        )
        self.category = CategoryFactory()
        self.barrier.categories.add(self.category)
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def test_status_is_serialized_consistently(self):
        expected_status = {
            "id": BarrierStatus.OPEN_PENDING,
            "name": BarrierStatus.name(BarrierStatus.OPEN_PENDING)
        }
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        data = PublicBarrierSerializer(pb).data
        assert expected_status == data["status"]
        assert expected_status == data["internal_status"]
        assert expected_status == data["latest_published_version"]["status"]

    def test_country_is_serialized_consistently(self):
        expected_country = {
            "id": "1f0be5c4-5d95-e211-a939-e4115bead28a",
            "name": "Singapore"
        }
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        data = PublicBarrierSerializer(pb).data
        assert expected_country == data["country"]
        assert expected_country == data["internal_country"]
        assert expected_country == data["latest_published_version"]["country"]

    def test_sectors_is_serialized_consistently(self):
        expected_sectors = [
            {"id": "9b38cecc-5f95-e211-a939-e4115bead28a", "name": "Chemicals"}
        ]
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        data = PublicBarrierSerializer(pb).data
        assert expected_sectors == data["sectors"]
        assert expected_sectors == data["internal_sectors"]
        assert expected_sectors == data["latest_published_version"]["sectors"]

    def test_all_sectors_is_serialized_consistently(self):
        expected_all_sectors = False
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        data = PublicBarrierSerializer(pb).data
        assert expected_all_sectors == data["all_sectors"]
        assert expected_all_sectors == data["internal_all_sectors"]
        assert expected_all_sectors == data["latest_published_version"]["all_sectors"]

    def test_categories_is_serialized_consistently(self):
        expected_categories = [
            {"id": self.category.id, "title": self.category.title}
        ]
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        data = PublicBarrierSerializer(pb).data
        assert expected_categories == data["categories"]
        assert expected_categories == data["internal_categories"]
        assert expected_categories == data["latest_published_version"]["categories"]
