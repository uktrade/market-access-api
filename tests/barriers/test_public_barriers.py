from datetime import datetime

import boto3
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
import dateutil.parser
from freezegun import freeze_time
from mock import patch
from rest_framework import status

from api.barriers.helpers import get_team_member_user_ids
from api.barriers.models import PublicBarrier, Barrier
from api.barriers.serializers import PublicBarrierSerializer
from api.barriers.serializers.public_barriers import public_barriers_to_json
from api.barriers.public_data import (
    public_barrier_data_json_file_content,
    versioned_folder, VersionedFile, latest_file,
)
from api.core.exceptions import ArchivingException
from api.core.test_utils import APITestMixin
from api.core.utils import read_file_from_s3, list_s3_public_data_files
from api.metadata.constants import PublicBarrierStatus, BarrierStatus

from moto import mock_s3

from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import CategoryFactory
from tests.user.factories import UserFactoryMixin


class PublicBarrierBaseTestCase(UserFactoryMixin, APITestMixin, TestCase):
    def get_public_barrier(self, barrier=None):
        barrier = barrier or BarrierFactory()
        url = reverse("public-barriers-detail", kwargs={"pk": barrier.id})
        response = self.api_client.get(url)
        return PublicBarrier.objects.get(pk=response.data["id"])

    def publish_barrier(self, pb=None, prepare=True, user=None):
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
        client = self.create_api_client(user=user)
        response = client.post(publish_url)

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
        assert 1 == Barrier.objects.count()
        assert 0 == PublicBarrier.objects.count()

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code

        assert 1 == Barrier.objects.count()
        assert 1 == PublicBarrier.objects.count()

    def test_public_barrier_default_values_at_creation(self):
        """
        Defaults should be set when the public barrier gets created.
        """
        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert not response.data["title"]
        assert not response.data["summary"]
        assert self.barrier.country == response.data["country"]["id"]
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
    def test_public_barrier_patch_as_standard_user(self):
        user = self.create_standard_user()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_patch_as_sifter(self):
        user = self.create_sifter()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    @freeze_time("2020-02-02")
    def test_public_barrier_patch_as_editor(self):
        user = self.create_editor()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_title == response.data["title"]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]

    @freeze_time("2020-02-02")
    def test_public_barrier_patch_as_publisher(self):
        """ Publishers can patch public barriers """
        user = self.create_publisher()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_title == response.data["title"]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]
        assert not response.data["summary"]
        assert not response.data["summary_updated_on"]

    @freeze_time("2020-02-02")
    def test_public_barrier_patch_as_admin(self):
        """ Admins can patch public barriers """
        user = self.create_admin()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_title == response.data["title"]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]
        assert not response.data["summary"]
        assert not response.data["summary_updated_on"]

    @freeze_time("2020-02-02")
    def test_public_barrier_patch_summary_as_publisher(self):
        """ Publishers can patch public barriers """
        user = self.create_publisher()
        client = self.create_api_client(user=user)
        public_summary = "New public facing summary!"
        payload = {"summary": public_summary}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_summary == response.data["summary"]
        assert "2020-02-02" == response.data["summary_updated_on"].split("T")[0]
        assert not response.data["title"]
        assert not response.data["title_updated_on"]

    # === READY ====
    def test_public_barrier_marked_ready_as_standard_user(self):
        """ Standard users cannot mark public barriers ready (to be published) """
        user = self.create_standard_user()
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_marked_ready_as_sifter(self):
        """ Sifters cannot mark public barriers ready (to be published) """
        user = self.create_sifter()
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_marked_ready_as_editor(self):
        """ Editors can mark public barriers ready (to be published) """
        user = self.create_editor()
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.READY == response.data["public_view_status"]

    def test_public_barrier_marked_ready_as_publisher(self):
        """ Publishers can mark public barriers ready (to be published) """
        user = self.create_publisher()
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.READY == response.data["public_view_status"]

    def test_public_barrier_marked_ready_as_admin(self):
        """ Admins can mark public barriers ready (to be published) """
        user = self.create_admin()
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.READY == response.data["public_view_status"]

    # === UNPREPARED ====
    def test_public_barrier_marked_unprepared_as_standard_user(self):
        """ Standard users cannot mark a public barriers unprepared (not ready) """
        user = self.create_standard_user()
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_marked_unprepared_as_sifter(self):
        """ Sifter cannot mark a public barriers unprepared (not ready) """
        user = self.create_sifter()
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_marked_unprepared_as_editor(self):
        """ Editors can mark a public barriers unprepared (not ready) """
        user = self.create_editor()
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.ELIGIBLE == response.data["public_view_status"]

    def test_public_barrier_marked_unprepared_as_publisher(self):
        """ Publishers can mark a public barriers unprepared (not ready) """
        user = self.create_publisher()
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.ELIGIBLE == response.data["public_view_status"]

    def test_public_barrier_marked_unprepared_as_admin(self):
        """ Admins can mark a public barriers unprepared (not ready) """
        user = self.create_admin()
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.ELIGIBLE == response.data["public_view_status"]

    # === IGNORE ALL CHANGES ====
    @freeze_time("2020-02-02")
    def test_public_barrier_ignore_all_changes_as_standard_user(self):
        """ Standard users cannot ignore all changes """
        user = self.create_standard_user()
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    @freeze_time("2020-02-02")
    def test_public_barrier_ignore_all_changes_as_sifter(self):
        """ Sifters cannot ignore all changes """
        user = self.create_sifter()
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    @freeze_time("2020-02-02")
    def test_public_barrier_ignore_all_changes_as_editor(self):
        """ Editors can ignore all changes """
        user = self.create_editor()
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert "2020-02-02" == response.data["summary_updated_on"].split("T")[0]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]

    @freeze_time("2020-02-02")
    def test_public_barrier_ignore_all_changes_as_publisher(self):
        """ Publishers can ignore all changes """
        user = self.create_publisher()
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert "2020-02-02" == response.data["summary_updated_on"].split("T")[0]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]

    @freeze_time("2020-02-02")
    def test_public_barrier_ignore_all_changes_as_admin(self):
        """ Admins can ignore all changes """
        user = self.create_admin()
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert "2020-02-02" == response.data["summary_updated_on"].split("T")[0]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]

    # === PUBLISH ====
    def test_public_barrier_publish_as_standard_user(self):
        """ Standard users are not allowed to publish public barriers """
        user = self.create_standard_user()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_publish_as_sifter(self):
        """ Sifters are not allowed to publish public barriers """
        user = self.create_sifter()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_publish_as_editor(self):
        """ Editors are not allowed to publish public barriers """
        user = self.create_editor()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_publish_as_publisher(self):
        """ Publishers are allowed to publish public barriers """
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.PUBLISHED == response.data["public_view_status"]
        assert response.data["first_published_on"]
        assert response.data["last_published_on"]
        assert not response.data["unpublished_on"]

    def test_public_barrier_publish_as_admin(self):
        """ Admins are allowed to publish public barriers """
        user = self.create_admin()
        pb, response = self.publish_barrier(user=user)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.PUBLISHED == response.data["public_view_status"]
        assert response.data["first_published_on"]
        assert response.data["last_published_on"]
        assert not response.data["unpublished_on"]

    def test_public_barrier_publish_creates_a_published_version(self):
        pb = self.get_public_barrier()

        assert not pb.published_versions
        assert not pb.latest_published_version

        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_new_published_version(self):
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == len(pb.published_versions["versions"])
        assert '1' == pb.published_versions["latest_version"]
        assert pb.latest_published_version

        pb.title = "Updating title to allow publishing."
        pb.public_view_status = PublicBarrierStatus.READY
        pb.save()
        pb, response = self.publish_barrier(pb=pb, user=user, prepare=False)

        assert status.HTTP_200_OK == response.status_code
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
        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert "Some title" == pb.latest_published_version.title
        assert "Some summary" == pb.latest_published_version.summary
        assert self.barrier.status == pb.latest_published_version.status
        assert str(self.barrier.country) == str(pb.latest_published_version.country)
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
        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

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
        assert str(self.barrier.country) == str(pb.latest_published_version.country)
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

        assert self.barrier.status != pb.status
        assert True is pb.internal_status_changed

        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.status == pb.status

    def test_public_barrier_publish_updates_country(self):
        angola_uuid = "985f66a0-5d95-e211-a939-e4115bead28a"
        singapore_uuid = "1f0be5c4-5d95-e211-a939-e4115bead28a"
        self.barrier.country = angola_uuid
        self.barrier.save()

        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        self.barrier.refresh_from_db()
        assert self.barrier.country == pb.country

        # Change barrier country
        self.barrier.country = singapore_uuid
        self.barrier.save()
        self.barrier.refresh_from_db()

        assert self.barrier.country != pb.country
        assert True is pb.internal_country_changed

        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.country == pb.country

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
        pb.refresh_from_db()

        assert self.barrier.sectors != pb.sectors
        assert True is pb.internal_sectors_changed

        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.sectors == pb.sectors

    def test_public_barrier_publish_updates_all_sectors(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert self.barrier.all_sectors == pb.all_sectors

        # Change barrier status
        self.barrier.all_sectors = True
        self.barrier.save()

        assert self.barrier.all_sectors != pb.all_sectors
        assert True is pb.internal_all_sectors_changed

        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert self.barrier.all_sectors == pb.all_sectors

    def test_public_barrier_publish_updates_categories(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])

        assert not pb.categories.all()

        category = CategoryFactory()
        self.barrier.categories.add(category)
        self.barrier.save()

        assert True is pb.internal_categories_changed

        user = self.create_publisher()
        pb, response = self.publish_barrier(pb=pb, user=user)

        assert status.HTTP_200_OK == response.status_code
        assert pb.categories.first()
        assert category.id == pb.categories.first().id

    # === UNPUBLISH ===
    def test_public_barrier_unpublish_as_standard_user(self):
        user = self.create_standard_user()
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_unpublish_as_sifter(self):
        user = self.create_sifter()
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_unpublish_as_editor(self):
        user = self.create_editor()
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_unpublish_as_publisher(self):
        user = self.create_publisher()
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.UNPUBLISHED == response.data["public_view_status"]
        assert response.data["unpublished_on"]

    def test_public_barrier_unpublish_as_admin(self):
        user = self.create_admin()
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.UNPUBLISHED == response.data["public_view_status"]
        assert response.data["unpublished_on"]

    def test_public_barrier_publish_resets_unpublished_on(self):
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        url = reverse("public-barriers-unpublish", kwargs={"pk": pb.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)
        assert status.HTTP_200_OK == response.status_code
        assert response.data["unpublished_on"]

        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code
        assert not response.data["unpublished_on"]
        assert not pb.unpublished_on

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
            country="1f0be5c4-5d95-e211-a939-e4115bead28a",  # Singapore
            sectors=['9b38cecc-5f95-e211-a939-e4115bead28a'],  # Chemicals
            status=BarrierStatus.OPEN_PENDING,
        )
        self.category = CategoryFactory()
        self.barrier.categories.add(self.category)
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def test_latest_published_version_fields(self):
        response = self.api_client.get(self.url)
        pb = PublicBarrier.objects.get(pk=response.data["id"])
        pb.publish()
        pb.refresh_from_db()

        data = PublicBarrierSerializer(pb).data
        published_version_fields = data["latest_published_version"].keys()
        assert "id" in published_version_fields
        assert "title" in published_version_fields
        assert "summary" in published_version_fields
        assert "status_date" in published_version_fields
        assert "is_resolved" in published_version_fields
        assert "location" in published_version_fields

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
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert data["is_resolved"] is False
        assert data["internal_is_resolved"] is False
        assert data["latest_published_version"]["is_resolved"] is False

    def test_country_is_serialized_consistently(self):
        expected_country = {
            "id": "1f0be5c4-5d95-e211-a939-e4115bead28a",
            "name": "Singapore",
            "trading_bloc": None
        }

        user = self.create_publisher()
        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert expected_country == data["country"]
        assert expected_country == data["internal_country"]
        assert expected_country == data["latest_published_version"]["country"]

    def test_sectors_is_serialized_consistently(self):
        expected_sectors = [
            {"id": "9b38cecc-5f95-e211-a939-e4115bead28a", "name": "Chemicals"}
        ]

        user = self.create_publisher()
        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert expected_sectors == data["sectors"]
        assert expected_sectors == data["internal_sectors"]
        assert expected_sectors == data["latest_published_version"]["sectors"]

    def test_all_sectors_is_serialized_consistently(self):
        expected_all_sectors = False

        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert expected_all_sectors == data["all_sectors"]
        assert expected_all_sectors == data["internal_all_sectors"]
        assert expected_all_sectors == data["latest_published_version"]["all_sectors"]

    def test_categories_is_serialized_consistently(self):
        expected_categories = [
            {"id": self.category.id, "title": self.category.title}
        ]

        user = self.create_publisher()
        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=user)
        assert status.HTTP_200_OK == response.status_code

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
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code
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
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code
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
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code
        assert False is pb.unpublished_changes
        assert False is pb.ready_to_be_published

    def test_ready_to_be_published_is_true_for_republish(self):
        """
        The case when the public barrier gets unpublished then republished without changes
        """
        # 1. Publish the barrier
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        assert False is pb.unpublished_changes
        assert False is pb.ready_to_be_published

        # 2. Unpublish the barrier
        url = reverse("public-barriers-unpublish", kwargs={"pk": pb.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        pb.refresh_from_db()
        assert pb.unpublished_on

        # 3. Review the changes
        #    once the changes are reviewed it should be ready to be published
        #    even without unpublished changes
        pb.public_view_status = PublicBarrierStatus.READY
        pb.save()
        pb.refresh_from_db()

        assert False is pb.unpublished_changes
        assert True is pb.ready_to_be_published


class TestPublicBarrierContributors(PublicBarrierBaseTestCase):
    """
    Users who make actions on the public barrier tab should be added
    to the Barrier Team as contributors automatically.
    """

    def setUp(self):
        self.publisher = self.create_publisher()
        self.client = self.create_api_client(user=self.publisher)
        self.barrier = BarrierFactory()
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def test_public_barrier_views_wont_add_user_as_contributor(self):
        assert 0 == get_team_member_user_ids(self.barrier.id).count()

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == get_team_member_user_ids(self.barrier.id).count()

    def test_public_barrier_patch_adds_user_as_contributor(self):
        assert 0 == get_team_member_user_ids(self.barrier.id).count()

        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = self.client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        members = get_team_member_user_ids(self.barrier.id)
        assert 1 == members.count()
        assert self.publisher.id == members.first()

    def test_public_barrier_marked_ready_adds_user_as_contributor(self):
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})
        response = self.client.post(url)

        assert status.HTTP_200_OK == response.status_code
        members = get_team_member_user_ids(self.barrier.id)
        assert 1 == members.count()
        assert self.publisher.id == members.first()

    def test_public_barrier_marked_unprepared_adds_user_as_contributor(self):
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})
        response = self.client.post(url)

        assert status.HTTP_200_OK == response.status_code
        members = get_team_member_user_ids(self.barrier.id)
        assert 1 == members.count()
        assert self.publisher.id == members.first()

    def test_public_barrier_ignore_all_changes_adds_user_as_contributor(self):
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})
        response = self.client.post(url)

        assert status.HTTP_200_OK == response.status_code
        members = get_team_member_user_ids(self.barrier.id)
        assert 1 == members.count()
        assert self.publisher.id == members.first()

    def test_public_barrier_publish_adds_user_as_contributor(self):
        assert 0 == get_team_member_user_ids(self.barrier.id).count()

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=self.publisher)

        assert status.HTTP_200_OK == response.status_code
        members = get_team_member_user_ids(self.barrier.id)
        assert 1 == members.count()
        assert self.publisher.id == members.first()

    def test_public_barrier_unpublish_adds_user_as_contributor(self):
        assert 0 == get_team_member_user_ids(self.barrier.id).count()

        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        response = self.client.post(url)

        assert status.HTTP_200_OK == response.status_code
        members = get_team_member_user_ids(self.barrier.id)
        assert 1 == members.count()
        assert self.publisher.id == members.first()


class TestArchivingBarriers(PublicBarrierBaseTestCase):

    def setUp(self):
        self.publisher = self.create_publisher()
        self.client = self.create_api_client(user=self.publisher)
        self.barrier = BarrierFactory()
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def test_can_archive_a_barrier_without_public_barrier(self):
        assert not self.barrier.archived
        assert not self.barrier.archived_on

        self.barrier.archive(self.publisher)

        assert self.barrier.archived
        assert self.barrier.archived_on

    def test_archiving_barrier_raises_when_published(self):
        assert not self.barrier.archived
        assert not self.barrier.archived_on

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=self.publisher)
        assert status.HTTP_200_OK == response.status_code

        with self.assertRaises(ArchivingException):
            self.barrier.archive(self.publisher)

            assert not self.barrier.archived
            assert not self.barrier.archived_on

    def test_archiving_barrier_when_unpublished(self):
        assert not self.barrier.archived
        assert not self.barrier.archived_on

        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=self.publisher)
        assert status.HTTP_200_OK == response.status_code

        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        response = self.client.post(url)
        assert status.HTTP_200_OK == response.status_code

        self.barrier.archive(self.publisher)

        assert self.barrier.archived
        assert self.barrier.archived_on


class TestPublicBarriersToPublicData(PublicBarrierBaseTestCase):

    def setUp(self):
        self.publisher = self.create_publisher()
        self.client = self.create_api_client(user=self.publisher)
        self.barrier = BarrierFactory()
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def create_mock_s3_bucket(self):
        conn = boto3.resource(
            's3',
            region_name=settings.PUBLIC_DATA_BUCKET_REGION
        )
        conn.create_bucket(Bucket=settings.PUBLIC_DATA_BUCKET)

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_data_file_gets_uploaded_to_s3(self):
        self.create_mock_s3_bucket()

        pb1, _ = self.publish_barrier(user=self.publisher)
        pb2, _ = self.publish_barrier(user=self.publisher)
        pb3, _ = self.publish_barrier(user=self.publisher)

        # Check data.json
        data_filename = f"{versioned_folder()}/data.json"
        obj = read_file_from_s3(data_filename)
        public_data = json.loads(obj.get()['Body'].read().decode())

        expected_ids = [pb1.id, pb2.id, pb3.id]
        assert "barriers" in public_data.keys()
        assert sorted(expected_ids) == sorted([b["id"] for b in public_data["barriers"]])

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_metadata_file_upload_to_s3(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)

        # Check metadata.json
        metadata_filename = f"{versioned_folder()}/metadata.json"
        obj = read_file_from_s3(metadata_filename)
        metadata = json.loads(obj.get()['Body'].read().decode())

        assert "release_date" in metadata.keys()
        today = datetime.today().strftime('%Y-%m-%d')
        assert today == metadata["release_date"]

    def test_data_json_file_content_task(self):
        pb1, _ = self.publish_barrier(user=self.publisher)
        pb2, _ = self.publish_barrier(user=self.publisher)

        data = public_barrier_data_json_file_content()

        assert "barriers" in data.keys()
        assert 2 == len(data["barriers"])

    @freeze_time("2020-05-20")
    def test_public_serializer(self):
        pb1, _ = self.publish_barrier(user=self.publisher)

        public_barriers_to_json()
        barrier = public_barriers_to_json()[0]

        assert pb1.id == barrier["id"]
        assert pb1.title == barrier["title"]
        assert pb1.summary == barrier["summary"]
        assert pb1.is_resolved == barrier["is_resolved"]
        assert pb1.status_date.isoformat() == barrier["status_date"]
        assert pb1.last_published_on == dateutil.parser.parse(barrier["last_published_on"])

    @patch("api.barriers.views.public_release_to_s3")
    def test_publish_calls_public_release(self, mock_release):
        pb, _ = self.publish_barrier(user=self.publisher)
        assert mock_release.called is True

    @patch("api.barriers.views.public_release_to_s3")
    def test_unpublish_calls_public_release(self, mock_release):
        pb, _ = self.publish_barrier(user=self.publisher)
        url = reverse("public-barriers-unpublish", kwargs={"pk": pb.barrier.id})

        client = self.create_api_client(user=self.publisher)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert mock_release.called is True

    @patch("api.barriers.views.public_release_to_s3")
    def test_ready_does_not_call_public_release(self, mock_release):
        _pb = self.get_public_barrier(self.barrier)
        url = reverse("public-barriers-ready", kwargs={"pk": self.barrier.id})

        client = self.create_api_client(user=self.publisher)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert mock_release.called is False

    @patch("api.barriers.views.public_release_to_s3")
    def test_unprepared_does_not_call_public_release(self, mock_release):
        _pb = self.get_public_barrier(self.barrier)
        url = reverse("public-barriers-unprepared", kwargs={"pk": self.barrier.id})

        client = self.create_api_client(user=self.publisher)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert mock_release.called is False

    @patch("api.barriers.views.public_release_to_s3")
    def test_ignore_all_changes_does_not_call_public_release(self, mock_release):
        _pb = self.get_public_barrier(self.barrier)
        url = reverse("public-barriers-ignore-all-changes", kwargs={"pk": self.barrier.id})

        client = self.create_api_client(user=self.publisher)
        response = client.post(url)

        assert status.HTTP_200_OK == response.status_code
        assert mock_release.called is False

    @patch("api.barriers.views.public_release_to_s3")
    def test_get_details_does_not_call_public_release(self, mock_release):
        _pb = self.get_public_barrier(self.barrier)
        url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

        client = self.create_api_client(user=self.publisher)
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert mock_release.called is False

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_versions_when_uploading_to_s3(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)
        file = latest_file()
        assert 'v1.0.1' == file.version_label

        pb, _ = self.publish_barrier(user=self.publisher)
        file = latest_file()
        assert 'v1.0.2' == file.version_label

    def test_versioned_file_version_as_float(self):
        file = VersionedFile("market-access/v1.5.101/data.json")
        assert 15.101 == file.version_as_float

    def test_versioned_file_next_version(self):
        file = VersionedFile("market-access/v1.0.1/data.json")
        assert "v1.0.2" == file.next_version

    def test_versioned_file_next_version_when_no_version_is_in_path(self):
        file = VersionedFile("data.json")
        assert "v1.0.1" == file.next_version

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_major_bump(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)
        file = latest_file()
        assert 'v1.0.1' == file.version_label
        assert 'v1.0.2' == file.next_version

        with override_settings(PUBLIC_DATA_MAJOR=2):
            pb, _ = self.publish_barrier(user=self.publisher)
            file = latest_file()
            assert 'v2.0.1' == file.version_label
            assert 'v2.0.2' == file.next_version

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_minor_bump(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)
        file = latest_file()
        assert 'v1.0.1' == file.version_label
        assert 'v1.0.2' == file.next_version

        with override_settings(PUBLIC_DATA_MINOR=5):
            pb, _ = self.publish_barrier(user=self.publisher)
            file = latest_file()
            assert 'v1.5.1' == file.version_label
            assert 'v1.5.2' == file.next_version

    @override_settings(PUBLIC_DATA_MINOR=10)
    def test_minor_throws_error(self):
        self.assertRaisesMessage(
            ImproperlyConfigured,
            "PUBLIC_DATA_MINOR should not be greater than 9"
        )

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_data_and_metadata_gets_the_same_version_on_publish(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)

        (data_file, metadata_file) = [VersionedFile(f) for f in list_s3_public_data_files()]
        assert "v1.0.1" == data_file.version_label
        assert "v1.0.1" == metadata_file.version_label
