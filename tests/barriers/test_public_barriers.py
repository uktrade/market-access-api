from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from api.barriers.models import PublicBarrier, BarrierInstance
from api.barriers.serializers import PublicBarrierSerializer
from api.core.test_utils import APITestMixin
from api.metadata.constants import PublicBarrierStatus, BarrierStatus
from api.metadata.utils import get_country
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import CategoryFactory


class PublicBarrierBaseTestCase(APITestMixin, TestCase):
    def get_public_barrier(self, barrier=None):
        barrier = barrier or BarrierFactory()
        url = reverse("public-barriers-detail", kwargs={"pk": barrier.id})
        response = self.api_client.get(url)
        return PublicBarrier.objects.get(pk=response.data["id"])

    def publish_barrier(self, pb=None, prepare=True):
        pb = pb or self.get_public_barrier()
        if prepare:
            # make sure the pubic barrier is ready to be published
            pb.public_view_status = PublicBarrierStatus.READY
            if not pb.title:
                pb.title = "Some title"
            if not pb.summary:
                pb.summary = "Some summary"
            pb.save()

        publish_url = reverse("public-barriers-publish", kwargs={"pk": pb.barrier.id})
        response = self.api_client.post(publish_url)

        pb.refresh_from_db()
        return pb, response


class TestPublicBarrier(PublicBarrierBaseTestCase):
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
        assert self.barrier.export_country == response.data["country"]["id"]
        assert self.barrier.sectors == [s["id"] for s in response.data["sectors"]]
        assert not response.data["categories"]

    def test_public_barrier_default_categories_at_creation(self):
        """
        Check that all categories are being set for the public barrier.
        """
        categories_count = 3
        categories = CategoryFactory.create_batch(categories_count)
        expected_category_ids = set([c.id for c in categories])
        self.barrier.categories.add(*categories)

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert categories_count == len(response.data["categories"])
        assert expected_category_ids == set([c["id"] for c in response.data["categories"]])

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
        pb, response = self.publish_barrier()

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.PUBLISHED == response.data["public_view_status"]
        assert response.data["first_published_on"]
        assert response.data["last_published_on"]
        assert not response.data["unpublished_on"]

    def test_public_barrier_publish_creates_a_published_version(self):
        pb = self.get_public_barrier()

        assert not pb.published_versions
        assert not pb.latest_published_version

        pb, _response = self.publish_barrier(pb=pb)

        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_new_published_version(self):
        pb, _response = self.publish_barrier()

        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

        pb.title = "Updating title to allow publishing."
        pb.public_view_status = PublicBarrierStatus.READY
        pb.save()
        pb, _response = self.publish_barrier(pb=pb, prepare=False)

        assert 2 == len(pb.published_versions["versions"])
        assert '2' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_latest_published_version_attributes(self):
        category = CategoryFactory()
        self.barrier.categories.add(category)
        self.barrier.sectors = ['9b38cecc-5f95-e211-a939-e4115bead28a']
        self.barrier.all_sectors = False
        self.barrier.save()

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb)

        assert status.HTTP_200_OK == response.status_code
        assert "Some title" == pb.latest_published_version.title
        assert "Some summary" == pb.latest_published_version.summary
        assert self.barrier.status == pb.latest_published_version.status
        assert str(self.barrier.export_country) == str(pb.latest_published_version.country)
        assert [str(s) for s in self.barrier.sectors] == [str(s) for s in pb.latest_published_version.sectors]
        assert False is pb.latest_published_version.all_sectors
        assert list(self.barrier.categories.all()) == list(pb.latest_published_version.categories.all())

    def test_public_barrier_latest_published_version_not_affected_by_updates(self):
        category = CategoryFactory()
        self.barrier.categories.add(category)
        self.barrier.sectors = ['9b38cecc-5f95-e211-a939-e4115bead28a']
        self.barrier.all_sectors = False
        self.barrier.status = BarrierStatus.OPEN_PENDING
        self.barrier.save()
        expected_status = BarrierStatus.OPEN_PENDING
        expected_sectors = ['9b38cecc-5f95-e211-a939-e4115bead28a']

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb)

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
        assert "Some title" == pb.latest_published_version.title
        assert "Some summary" == pb.latest_published_version.summary
        assert expected_status == pb.latest_published_version.status
        assert str(self.barrier.export_country) == str(pb.latest_published_version.country)
        assert [str(s) for s in expected_sectors] == [str(s) for s in pb.latest_published_version.sectors]
        assert False is pb.latest_published_version.all_sectors
        assert list(self.barrier.categories.all()) == list(pb.latest_published_version.categories.all())

    def test_public_barrier_publish_updates_status(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert self.barrier.status == pb.status

        # Change barrier status
        self.barrier.status = BarrierStatus.OPEN_IN_PROGRESS
        self.barrier.save()
        self.barrier.refresh_from_db()

        # make sure the pubic barrier is ready to be published
        pb.public_view_status = PublicBarrierStatus.READY
        pb.title = "Some title"
        pb.summary = "Some summary"
        pb.save()
        pb.refresh_from_db()

        assert self.barrier.status != pb.status
        assert True is pb.internal_status_changed

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        pb.refresh_from_db()
        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.status == pb.status

    def test_public_barrier_publish_updates_country(self):
        angola_uuid = "985f66a0-5d95-e211-a939-e4115bead28a"
        singapore_uuid = "1f0be5c4-5d95-e211-a939-e4115bead28a"
        self.barrier.export_country = angola_uuid
        self.barrier.save()

        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        self.barrier.refresh_from_db()
        assert self.barrier.export_country == pb.country

        # Change barrier country
        self.barrier.export_country = singapore_uuid
        self.barrier.save()
        self.barrier.refresh_from_db()

        # make sure the pubic barrier is ready to be published
        pb.public_view_status = PublicBarrierStatus.READY
        pb.title = "Some title"
        pb.summary = "Some summary"
        pb.save()
        pb.refresh_from_db()

        assert self.barrier.export_country != pb.country
        assert True is pb.internal_country_changed

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        pb.refresh_from_db()
        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.export_country == pb.country

    def test_public_barrier_publish_updates_sectors(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert pb.barrier.sectors == pb.sectors

        self.barrier.sectors = [
            "9538cecc-5f95-e211-a939-e4115bead28a",  # Aerospace
            "9b38cecc-5f95-e211-a939-e4115bead28a",  # Chemicals
        ]
        self.barrier.save()
        self.barrier.refresh_from_db()

        # make sure the pubic barrier is ready to be published
        pb.public_view_status = PublicBarrierStatus.READY
        pb.title = "Some title"
        pb.summary = "Some summary"
        pb.save()
        pb.refresh_from_db()

        assert self.barrier.sectors != pb.sectors
        assert True is pb.internal_sectors_changed

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code

        pb.refresh_from_db()
        assert self.barrier.sectors == pb.sectors

    def test_public_barrier_publish_updates_all_sectors(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert self.barrier.all_sectors == pb.all_sectors

        # Change barrier status
        self.barrier.all_sectors = True
        self.barrier.save()

        # make sure the pubic barrier is ready to be published
        pb.public_view_status = PublicBarrierStatus.READY
        pb.title = "Some title"
        pb.summary = "Some summary"
        pb.save()
        pb.refresh_from_db()

        assert self.barrier.all_sectors != pb.all_sectors
        assert True is pb.internal_all_sectors_changed

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        pb.refresh_from_db()
        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.all_sectors == pb.all_sectors

    def test_public_barrier_publish_updates_categories(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert not pb.categories.all()

        category = CategoryFactory()
        self.barrier.categories.add(category)
        self.barrier.save()

        # make sure the pubic barrier is ready to be published
        pb.public_view_status = PublicBarrierStatus.READY
        pb.title = "Some title"
        pb.summary = "Some summary"
        pb.save()

        assert True is pb.internal_categories_changed

        url = reverse("public-barriers-publish", kwargs={"pk": self.barrier.id})
        response = self.api_client.post(url)

        assert status.HTTP_200_OK == response.status_code

        pb.refresh_from_db()
        assert pb.categories.first()
        assert category.id == pb.categories.first().id

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


class TestPublicBarrierSerializer(PublicBarrierBaseTestCase):

    def setUp(self):
        self.barrier = BarrierFactory(
            export_country="1f0be5c4-5d95-e211-a939-e4115bead28a",  # Singapore
            sectors=['9b38cecc-5f95-e211-a939-e4115bead28a'],  # Chemicals
            status=BarrierStatus.OPEN_PENDING
        )
        self.category = CategoryFactory()
        self.barrier.categories.add(self.category)
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def test_empty_title_field_gets_serialized_to_empty_string(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        assert not pb.title

        data = PublicBarrierSerializer(pb).data
        assert "" == data["title"]

    def test_empty_summary_field_gets_serialized_to_empty_string(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        assert not pb.summary

        data = PublicBarrierSerializer(pb).data
        assert "" == data["summary"]

    def test_status_is_serialized_consistently(self):
        expected_status = {
            "id": BarrierStatus.OPEN_PENDING,
            "name": BarrierStatus.name(BarrierStatus.OPEN_PENDING)
        }

        pb, response = self.publish_barrier()

        data = PublicBarrierSerializer(pb).data
        assert expected_status == data["status"]
        assert expected_status == data["internal_status"]
        assert expected_status == data["latest_published_version"]["status"]

    def test_country_is_serialized_consistently(self):
        expected_country = {
            "id": "1f0be5c4-5d95-e211-a939-e4115bead28a",
            "name": "Singapore"
        }

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb)

        data = PublicBarrierSerializer(pb).data
        assert expected_country == data["country"]
        assert expected_country == data["internal_country"]
        assert expected_country == data["latest_published_version"]["country"]

    def test_sectors_is_serialized_consistently(self):
        expected_sectors = [
            {"id": "9b38cecc-5f95-e211-a939-e4115bead28a", "name": "Chemicals"}
        ]

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb)

        data = PublicBarrierSerializer(pb).data
        assert expected_sectors == data["sectors"]
        assert expected_sectors == data["internal_sectors"]
        assert expected_sectors == data["latest_published_version"]["sectors"]

    def test_all_sectors_is_serialized_consistently(self):
        expected_all_sectors = False

        pb, response = self.publish_barrier()

        data = PublicBarrierSerializer(pb).data
        assert expected_all_sectors == data["all_sectors"]
        assert expected_all_sectors == data["internal_all_sectors"]
        assert expected_all_sectors == data["latest_published_version"]["all_sectors"]

    def test_categories_is_serialized_consistently(self):
        expected_categories = [
            {"id": self.category.id, "title": self.category.title}
        ]

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb)

        data = PublicBarrierSerializer(pb).data
        assert expected_categories == data["categories"]
        assert expected_categories == data["internal_categories"]
        assert expected_categories == data["latest_published_version"]["categories"]


class TestPublicBarrierFlags(PublicBarrierBaseTestCase):

    def test_status_of_flags_after_public_barrier_creation(self):
        pb = self.get_public_barrier()

        assert False is pb.internal_title_changed
        assert False is pb.title_changed
        assert False is pb.internal_summary_changed
        assert False is pb.summary_changed
        assert False is pb.internal_status_changed
        assert False is pb.internal_country_changed
        assert False is pb.internal_sectors_changed
        assert False is pb.internal_all_sectors_changed
        assert False is pb.internal_sectors_changed
        assert False is pb.internal_categories_changed
        assert False is pb.ready_to_be_published

    def test_title_changed_flag_returns_false(self):
        # There's no change to the title after publishing
        pb, _response = self.publish_barrier()
        assert False is pb.title_changed

    def test_title_changed_flag_returns_true(self):
        # There's an update to the title after publishing
        pb, _response = self.publish_barrier()
        pb.title = "New title!!"
        pb.save()
        pb.refresh_from_db()

        assert True is pb.title_changed

    def test_summary_changed_flag_returns_false(self):
        # There's no change to the summary after publishing
        pb, _response = self.publish_barrier()
        assert False is pb.summary_changed

    def test_summary_changed_flag_returns_true(self):
        # There's an update to the summary after publishing
        pb, _response = self.publish_barrier()
        pb.summary = "New summary!!"
        pb.save()
        pb.refresh_from_db()

        assert True is pb.summary_changed

    def test_ready_to_be_published_after_init(self):
        pb = self.get_public_barrier()
        assert False is pb.ready_to_be_published

    def test_ready_to_be_published_is_false_when_status_is_not_ready(self):
        statuses = [
            PublicBarrierStatus.UNKNOWN,
            PublicBarrierStatus.INELIGIBLE,
            PublicBarrierStatus.ELIGIBLE,
            PublicBarrierStatus.PUBLISHED,
            PublicBarrierStatus.UNPUBLISHED,
        ]

        for s in statuses:
            with self.subTest(s=s):
                pb, _response = self.publish_barrier()
                pb.public_view_status = s
                pb.save()
                pb.refresh_from_db()
                assert False is pb.ready_to_be_published

    def test_ready_to_be_published_is_false_when_title_is_none(self):
        pb = self.get_public_barrier()
        pb.title = None
        assert False is pb.ready_to_be_published

    def test_ready_to_be_published_is_false_when_summary_is_none(self):
        pb = self.get_public_barrier()
        pb.summary = None
        assert False is pb.ready_to_be_published

    def test_ready_to_be_published_is_false_when_no_unpublished_changes(self):
        pb, _response = self.publish_barrier()
        assert False is pb.unpublished_changes
        assert False is pb.ready_to_be_published
