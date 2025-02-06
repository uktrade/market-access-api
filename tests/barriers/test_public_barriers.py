import json
import logging
from datetime import datetime, timedelta
from typing import Dict
from uuid import uuid4

import boto3
import dateutil.parser
import freezegun
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from mock import patch
from moto import mock_s3
from rest_framework import status

from api.barriers.helpers import get_team_member_user_ids
from api.barriers.models import Barrier, PublicBarrier
from api.barriers.public_data import (
    VersionedFile,
    get_public_data_content,
    latest_file,
    versioned_folder,
)
from api.barriers.serializers import PublicBarrierSerializer
from api.barriers.serializers.public_barriers import PublicPublishedVersionSerializer
from api.collaboration.models import TeamMember
from api.core.exceptions import ArchivingException
from api.core.test_utils import APITestMixin
from api.core.utils import list_s3_public_data_files, read_file_from_s3
from api.interactions.models import PublicBarrierNote
from api.metadata.constants import BarrierStatus, PublicBarrierStatus
from api.metadata.models import Organisation
from tests.barriers.factories import BarrierFactory
from tests.user.factories import UserFactoryMixin

freezegun.configure(extend_ignore_list=["transformers"])

logger = logging.getLogger(__name__)


class PublicBarrierBaseTestCase(UserFactoryMixin, APITestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.barrier: Barrier = BarrierFactory()
        self.url = self.get_barrier_url(barrier=self.barrier)

    def get_barrier_url(self, barrier):
        return reverse("public-barriers-detail", kwargs={"pk": barrier.id})

    def get_public_barrier(self, barrier=None):
        barrier = barrier or BarrierFactory()
        url = reverse("public-barriers-detail", kwargs={"pk": barrier.id})
        response = self.api_client.get(url)
        return PublicBarrier.objects.get(pk=response.data["id"])

    def publish_barrier(
        self,
        pb: PublicBarrier = None,
        prepare: bool = True,
        user=None,
        barrier: Barrier = None,
    ):
        pb = pb or self.get_public_barrier(barrier=barrier)
        if prepare:
            # make sure the pubic barrier is ready to be published
            pb.public_view_status = PublicBarrierStatus.PUBLISHING_PENDING
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


class TestPublicBarrierListViewset(PublicBarrierBaseTestCase):
    def test_pb_list(self):
        url = reverse("public-barriers-list")
        barrier2 = BarrierFactory()
        barrier3 = BarrierFactory()

        assert 3 == PublicBarrier.objects.count()

        r = self.api_client.get(url)

        assert 200 == r.status_code
        assert 3 == r.data["count"]
        assert {
            self.barrier.public_barrier.id,
            barrier2.public_barrier.id,
            barrier3.public_barrier.id,
        } == {i["id"] for i in r.data["results"]}

    def test_pb_list_region_filter(self):
        country_id = "9f5f66a0-5d95-e211-a939-e4115bead28a"  # Australia
        region_id = "04a7cff0-03dd-4677-aa3c-12dd8426f0d7"  # Asia-Pacific
        url = f'{reverse("public-barriers-list")}?region={region_id}'

        barrier1 = BarrierFactory(country=country_id)
        pb1 = self.get_public_barrier(barrier1)
        pb1, _ = self.publish_barrier(pb1)

        pb2, _ = self.publish_barrier()

        r = self.api_client.get(url)

        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {pb1.id} == {i["id"] for i in r.data["results"]}

    def test_pb_list_organisation_filter(self):
        org1 = Organisation.objects.get(id=1)
        barrier1 = BarrierFactory()
        barrier1.organisations.add(org1)
        org2 = Organisation.objects.get(id=2)
        barrier2 = BarrierFactory()
        barrier2.organisations.add(org2)

        pb1 = self.get_public_barrier(barrier1)
        pb1, _ = self.publish_barrier(pb1)
        pb2 = self.get_public_barrier(barrier2)
        pb2, _ = self.publish_barrier(pb2)
        pb3 = self.get_public_barrier(self.barrier)
        pb3, _ = self.publish_barrier(pb3)

        assert 3 == PublicBarrier.objects.count()

        url = f'{reverse("public-barriers-list")}?organisation={org1.id}'
        r = self.api_client.get(url)

        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {pb1.id} == {i["id"] for i in r.data["results"]}

    def test_pb_list_organisation_filter_with_multiple_values(self):
        org1 = Organisation.objects.get(id=1)
        barrier1 = BarrierFactory()
        barrier1.organisations.add(org1)
        org2 = Organisation.objects.get(id=2)
        barrier2 = BarrierFactory()
        barrier2.organisations.add(org2)

        pb1 = self.get_public_barrier(barrier1)
        pb1, _ = self.publish_barrier(pb1)
        pb2 = self.get_public_barrier(barrier2)
        pb2, _ = self.publish_barrier(pb2)
        pb3 = self.get_public_barrier(self.barrier)
        pb3, _ = self.publish_barrier(pb3)

        assert 3 == PublicBarrier.objects.count()

        url = f'{reverse("public-barriers-list")}?organisation={org1.id},{org2.id}'
        r = self.api_client.get(url)

        assert 200 == r.status_code
        assert 2 == r.data["count"]
        assert {pb1.id, pb2.id} == {i["id"] for i in r.data["results"]}

    def test_pb_list_status_filter(self):
        barriers: Dict[int, Barrier] = {}
        for status_code, status_name in PublicBarrierStatus.choices:
            if status_code == PublicBarrierStatus.UNKNOWN:
                # skip because self.barrier public_barrier is already in this status
                # we only want 1 public barrier of each status
                barriers[status_code] = self.barrier
                continue
            barriers[status_code] = BarrierFactory(
                public_barrier___public_view_status=status_code
            )

        def get_list_for_status(status_code):
            url = f'{reverse("public-barriers-list")}?status={status_code}'
            return self.api_client.get(url)

        for status_code, status_name in PublicBarrierStatus.choices:
            r = get_list_for_status(status_code)
            public_barrier = barriers[status_code].public_barrier
            assert 200 == r.status_code
            assert 1 == r.data["count"]
            assert {public_barrier.id} == {i["id"] for i in r.data["results"]}

        # test filtering on multiple statuses

        r = get_list_for_status(
            ",".join(
                [
                    str(PublicBarrierStatus.PUBLISHING_PENDING),
                    str(PublicBarrierStatus.ALLOWED),
                ]
            )
        )

        public_barrier1 = barriers[
            PublicBarrierStatus.PUBLISHING_PENDING
        ].public_barrier
        public_barrier2 = barriers[PublicBarrierStatus.ALLOWED].public_barrier
        assert 200 == r.status_code
        assert 2 == r.data["count"]
        assert {public_barrier1.id, public_barrier2.id} == {
            i["id"] for i in r.data["results"]
        }

        # Test special status 'changed'
        published_barrier = barriers[PublicBarrierStatus.PUBLISHING_PENDING]

        published_barrier.sectors = ["8a38cecc-5f95-e211-a939-e4115bead28a"]
        published_barrier.save()
        published_barrier.refresh_from_db()
        published_barrier.public_barrier.publish()
        published_barrier.public_barrier.last_published_on = datetime.now() - timedelta(
            days=30
        )
        published_barrier.public_barrier.published_versions = {
            "versions": {
                "0": {
                    "published_on": f"{ datetime.now()}",
                }
            }
        }
        published_barrier.public_barrier.save()
        published_barrier.refresh_from_db()
        published_barrier.sectors = ["9b38cecc-5f95-e211-a939-e4115bead28a"]
        published_barrier.save()
        published_barrier.refresh_from_db()

        r = get_list_for_status("changed")
        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {published_barrier.id} == {i["internal_id"] for i in r.data["results"]}

    def test_pb_list_country_filter(self):
        country_id = "9f5f66a0-5d95-e211-a939-e4115bead28a"
        barrier = BarrierFactory(country=country_id)

        # now we have 2 barriers with 2 separate countries

        def get_list_for_country(country):
            url = f'{reverse("public-barriers-list")}?country={country}'
            return self.api_client.get(url)

        r = get_list_for_country(country_id)
        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {barrier.public_barrier.id} == {i["id"] for i in r.data["results"]}

        r = get_list_for_country(self.barrier.country)
        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {self.barrier.public_barrier.id} == {i["id"] for i in r.data["results"]}

        r = get_list_for_country(",".join([self.barrier.country, country_id]))
        assert 200 == r.status_code
        assert 2 == r.data["count"]
        assert {self.barrier.public_barrier.id, barrier.public_barrier.id} == {
            i["id"] for i in r.data["results"]
        }

    def test_pb_list_sector_filter(self):
        sector1 = uuid4()
        sector2 = uuid4()
        sector3 = self.barrier.sectors[0]
        barrier = BarrierFactory(sectors=[sector1, sector2, sector3])

        # now we have 2 barriers with 2 separate countries

        def get_list_for_sector(sector):
            url = f'{reverse("public-barriers-list")}?sector={sector}'
            return self.api_client.get(url)

        r = get_list_for_sector(sector3)
        assert 200 == r.status_code
        assert 2 == r.data["count"]
        assert {barrier.public_barrier.id, self.barrier.public_barrier.id} == {
            i["id"] for i in r.data["results"]
        }

        r = get_list_for_sector(sector1)
        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {barrier.public_barrier.id} == {i["id"] for i in r.data["results"]}

        r = get_list_for_sector(",".join([str(sector2), str(sector3)]))
        assert 200 == r.status_code
        assert 2 == r.data["count"]
        assert {barrier.public_barrier.id, self.barrier.public_barrier.id} == {
            i["id"] for i in r.data["results"]
        }

        r = get_list_for_sector(",".join([str(sector1), str(sector2)]))
        assert 200 == r.status_code
        assert 1 == r.data["count"]
        assert {barrier.public_barrier.id} == {i["id"] for i in r.data["results"]}

    def test_pb_list_returns_latest_note_for_items(self):
        url = reverse("public-barriers-list")
        pb1, _ = self.publish_barrier(barrier=self.barrier)

        with freezegun.freeze_time("2020-02-02"):
            _note1 = PublicBarrierNote.objects.create(
                public_barrier=pb1, text="wibble", created_by=self.mock_user
            )
        with freezegun.freeze_time("2020-02-03"):
            note2 = PublicBarrierNote.objects.create(
                public_barrier=pb1, text="wobble", created_by=self.mock_user
            )

        r = self.api_client.get(url)

        assert 2 == pb1.notes.count()
        assert 1 == len(r.data["results"])

        assert 200 == r.status_code
        assert note2.text == r.data["results"][0]["latest_note"].get("text")

    def test_pb_list_returns_none_for_latest_note(self):
        url = reverse("public-barriers-list")
        pb1, _ = self.publish_barrier()

        r = self.api_client.get(url)

        assert 200 == r.status_code
        assert not r.data["results"][0]["latest_note"]


class TestPublicBarrier(PublicBarrierBaseTestCase):
    def test_public_barrier_gets_created_when_a_barrier_is_created(self):
        """
        A corresponding public barrier gets created when a barrier is initially created.
        """
        assert 1 == Barrier.objects.count()
        assert 1 == PublicBarrier.objects.count()

        # A fetch request shouldn't create additional public barriers
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
        assert not response.data["last_published_on"]
        assert not response.data["first_published_on"]
        assert not response.data["unpublished_on"]
        assert not response.data["unpublished_changes"]
        assert not response.data["ready_to_be_published"]
        assert self.barrier.reported_on == dateutil.parser.parse(
            response.data["reported_on"]
        )

    # === PATCH ===
    def test_public_barrier_patch_as_standard_user(self):
        user = self.create_standard_user()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    @freezegun.freeze_time("2020-02-02")
    def test_public_barrier_patch_as_approver(self):
        user = self.create_approver()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"title": public_title}
        response = client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_title == response.data["title"]
        assert "2020-02-02" == response.data["title_updated_on"].split("T")[0]

    @freezegun.freeze_time("2020-02-02")
    def test_public_barrier_patch_as_publisher(self):
        """Publishers can patch public barriers"""
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

    @freezegun.freeze_time("2020-02-02")
    def test_public_barrier_patch_as_admin(self):
        """Admins can patch public barriers"""
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

    @freezegun.freeze_time("2020-02-02")
    def test_public_barrier_patch_summary_as_publisher(self):
        """Publishers can patch public barriers"""
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

    # === PUBLISH ====
    def test_public_barrier_publish_as_standard_user(self):
        """Standard users are not allowed to publish public barriers"""
        user = self.create_standard_user()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_publish_as_approver(self):
        """Editors are not allowed to publish public barriers"""
        user = self.create_approver()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_publish_as_publisher(self):
        """Publishers are allowed to publish public barriers"""
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)

        assert (
            TeamMember.objects.filter(
                user=user, barrier=pb.barrier, role=TeamMember.PUBLIC_PUBLISHER
            ).count()
            == 1
        )
        assert status.HTTP_200_OK == response.status_code
        assert PublicBarrierStatus.PUBLISHED == response.data["public_view_status"]
        assert response.data["first_published_on"]
        assert response.data["last_published_on"]
        assert not response.data["unpublished_on"]

    def test_public_barrier_publish_as_admin(self):
        """Admins are allowed to publish public barriers"""
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
        assert "1" == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_new_published_version(self):
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == len(pb.published_versions["versions"])
        assert "1" == pb.published_versions["latest_version"]
        assert pb.latest_published_version

        pb.title = "Updating title to allow publishing."
        pb.public_view_status = PublicBarrierStatus.PUBLISHING_PENDING
        pb.save()
        pb, response = self.publish_barrier(pb=pb, user=user, prepare=False)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == len(pb.published_versions["versions"])
        assert "2" == pb.published_versions["latest_version"]
        assert pb.latest_published_version

    def test_public_barrier_latest_published_version_attributes(self):
        self.barrier.sectors = ["9b38cecc-5f95-e211-a939-e4115bead28a"]
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
        assert [str(s) for s in self.barrier.sectors] == [
            str(s) for s in pb.latest_published_version.sectors
        ]
        assert False is pb.latest_published_version.all_sectors

    def test_public_barrier_latest_published_version_not_affected_by_updates(self):
        self.barrier.sectors = ["9b38cecc-5f95-e211-a939-e4115bead28a"]
        self.barrier.all_sectors = False
        self.barrier.status = BarrierStatus.OPEN_PENDING
        self.barrier.save()
        expected_status = BarrierStatus.OPEN_PENDING
        expected_sectors = ["9b38cecc-5f95-e211-a939-e4115bead28a"]

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
        assert "1" == pb.published_versions["latest_version"]

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert "Some title" == pb.latest_published_version.title
        assert "Some summary" == pb.latest_published_version.summary
        assert expected_status == pb.latest_published_version.status
        assert str(self.barrier.country) == str(pb.latest_published_version.country)
        assert [str(s) for s in expected_sectors] == [
            str(s) for s in pb.latest_published_version.sectors
        ]
        assert False is pb.latest_published_version.all_sectors

    # === UNPUBLISH ===
    def test_public_barrier_unpublish_as_standard_user(self):
        user = self.create_standard_user()
        url = reverse("public-barriers-unpublish", kwargs={"pk": self.barrier.id})
        client = self.create_api_client(user=user)
        response = client.post(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_public_barrier_unpublish_as_approver(self):
        user = self.create_approver()
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

    def test_report_public_barrier_title_as_standard_user(self):
        user = self.create_standard_user()
        client = self.create_api_client(user=user)
        public_title = "New public facing title!"
        payload = {"values": {"title": public_title}}

        url = reverse(
            "public-barriers-report-public-barrier-title",
            kwargs={"pk": self.barrier.id},
        )
        client = self.create_api_client(user=user)
        response = client.post(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_title == response.data["title"]

    def test_report_public_barrier_summary_as_standard_user(self):
        user = self.create_standard_user()
        client = self.create_api_client(user=user)
        public_summary = "New public facing summary!"
        payload = {"values": {"summary": public_summary}}

        url = reverse(
            "public-barriers-report-public-barrier-summary",
            kwargs={"pk": self.barrier.id},
        )
        client = self.create_api_client(user=user)
        response = client.post(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert public_summary == response.data["summary"]


class TestPublicBarrierSerializer(PublicBarrierBaseTestCase):
    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory(
            country="37afd8d0-5d95-e211-a939-e4115bead28a",  # Yemen
            sectors=["9b38cecc-5f95-e211-a939-e4115bead28a"],  # Chemicals
            status=BarrierStatus.OPEN_PENDING,
        )
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
        assert data["latest_published_version"]["is_resolved"] is False

    def test_country_is_serialized_consistently(self):
        expected_country = {
            "id": "37afd8d0-5d95-e211-a939-e4115bead28a",
            "name": "Yemen",
            "trading_bloc": None,
        }

        user = self.create_publisher()
        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert expected_country == data["country"]
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
        assert expected_sectors == data["latest_published_version"]["sectors"]

    def test_all_sectors_is_serialized_consistently(self):
        expected_all_sectors = False

        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert expected_all_sectors == data["all_sectors"]
        assert expected_all_sectors == data["latest_published_version"]["all_sectors"]

    def test_internal_main_sector_in_latest_published_version(self):
        user = self.create_publisher()
        pb = self.get_public_barrier(self.barrier)
        pb, response = self.publish_barrier(pb=pb, user=user)
        assert status.HTTP_200_OK == response.status_code

        data = PublicBarrierSerializer(pb).data
        assert (
            data["latest_published_version"]["main_sector"]["name"]
            == "Consumer and retail"
        )


class TestPublicBarrierFlags(PublicBarrierBaseTestCase):
    def test_status_of_flags_after_public_barrier_creation(self):
        pb = self.get_public_barrier()
        assert pb.ready_to_be_published is False

    def test_ready_to_be_published_is_false_when_status_is_not_ready_or_unpublished(
        self,
    ):
        statuses = [
            PublicBarrierStatus.UNKNOWN,
            PublicBarrierStatus.NOT_ALLOWED,
            PublicBarrierStatus.ALLOWED,
            PublicBarrierStatus.PUBLISHED,
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
        assert not pb.unpublished_changes
        assert not pb.ready_to_be_published

    def test_ready_to_be_published_is_true_for_republish(self):
        """
        The case when the public barrier gets unpublished then republished without changes
        """
        # 1. Publish the barrier
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        assert not pb.unpublished_changes
        assert not pb.ready_to_be_published

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
        pb.public_view_status = PublicBarrierStatus.PUBLISHING_PENDING
        pb.save()
        pb.refresh_from_db()

        assert not pb.unpublished_changes
        assert pb.ready_to_be_published

    def test_changed_since_published(self):
        """
        The case when the public barrier gets published and has a field changed
        """
        # 1. Publish the barrier
        user = self.create_publisher()
        pb, response = self.publish_barrier(user=user)
        assert status.HTTP_200_OK == response.status_code

        assert not pb.unpublished_changes
        assert not pb.changed_since_published

        # 2. Change a field that will trigger changed_since_published
        pb.barrier.sectors = []
        pb.barrier.save()

        assert "sectors" in pb.unpublished_changes
        pb.refresh_from_db()
        assert pb.changed_since_published


class TestPublicBarrierContributors(PublicBarrierBaseTestCase):
    """
    Users who make actions on the public barrier tab should be added
    to the Barrier Team as contributors automatically.
    """

    def setUp(self):
        super().setUp()
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
        super().setUp()
        self.publisher = self.create_publisher()
        self.client = self.create_api_client(user=self.publisher)
        self.barrier: Barrier = BarrierFactory()
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

        pb = self.get_public_barrier(barrier=self.barrier)
        pb, response = self.publish_barrier(
            pb=pb, user=self.publisher, prepare=True, barrier=self.barrier
        )
        assert status.HTTP_200_OK == response.status_code
        assert pb.id == self.barrier.public_barrier.id
        self.barrier.refresh_from_db()
        assert (
            self.barrier.public_barrier.public_view_status
            == PublicBarrierStatus.PUBLISHED
        )

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
        super().setUp()
        self.publisher = self.create_publisher()
        self.client = self.create_api_client(user=self.publisher)
        self.barrier = BarrierFactory()
        self.url = reverse("public-barriers-detail", kwargs={"pk": self.barrier.id})

    def create_mock_s3_bucket(self):
        conn = boto3.resource("s3", region_name=settings.PUBLIC_DATA_BUCKET_REGION)
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
        public_data = json.loads(obj.get()["Body"].read().decode())

        expected_ids = [pb1.id.hashid, pb2.id.hashid, pb3.id.hashid]
        assert "barriers" in public_data.keys()
        assert sorted(expected_ids) == sorted(
            [b["id"] for b in public_data["barriers"]]
        )

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_metadata_file_upload_to_s3(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)

        # Check metadata.json
        metadata_filename = f"{versioned_folder()}/metadata.json"
        obj = read_file_from_s3(metadata_filename)
        metadata = json.loads(obj.get()["Body"].read().decode())

        assert "release_date" in metadata.keys()
        today = datetime.today().strftime("%Y-%m-%d")
        assert today == metadata["release_date"]

    def test_data_json_file_content_task(self):
        pb1, _ = self.publish_barrier(user=self.publisher)
        pb2, _ = self.publish_barrier(user=self.publisher)

        data = get_public_data_content()

        assert "barriers" in data.keys()
        assert 2 == len(data["barriers"])

    @freezegun.freeze_time("2020-05-20")
    def test_public_serializer(self):
        pb1, _ = self.publish_barrier(user=self.publisher)
        barrier = PublicPublishedVersionSerializer(pb1).data

        assert pb1.id == barrier["id"]
        assert pb1.title == barrier["title"]
        assert pb1.summary == barrier["summary"]
        assert pb1.is_resolved == barrier["is_resolved"]
        assert pb1.status_date.isoformat() == barrier["status_date"]
        assert pb1.last_published_on == dateutil.parser.parse(
            barrier["last_published_on"]
        )
        assert pb1.reported_on == dateutil.parser.parse(barrier["reported_on"])
        # as the sector and the main sector in the list of sectors
        assert len(barrier["sectors"]) == 2
        assert barrier["sectors"][0]["name"] == "Consumer and retail"

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
        assert "v1.0.1" == file.version_label

        pb, _ = self.publish_barrier(user=self.publisher)
        file = latest_file()
        assert "v1.0.2" == file.version_label

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
        assert "v1.0.1" == file.version_label
        assert "v1.0.2" == file.next_version

        with override_settings(PUBLIC_DATA_MAJOR=2):
            pb, _ = self.publish_barrier(user=self.publisher)
            file = latest_file()
            assert "v2.0.1" == file.version_label
            assert "v2.0.2" == file.next_version

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_minor_bump(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)
        file = latest_file()
        assert "v1.0.1" == file.version_label
        assert "v1.0.2" == file.next_version

        with override_settings(PUBLIC_DATA_MINOR=5):
            pb, _ = self.publish_barrier(user=self.publisher)
            file = latest_file()
            assert "v1.5.1" == file.version_label
            assert "v1.5.2" == file.next_version

    @override_settings(PUBLIC_DATA_MINOR=10)
    def test_minor_throws_error(self):
        self.assertRaisesMessage(
            ImproperlyConfigured, "PUBLIC_DATA_MINOR should not be greater than 9"
        )

    @mock_s3
    @override_settings(PUBLIC_DATA_TO_S3_ENABLED=True)
    def test_data_and_metadata_gets_the_same_version_on_publish(self):
        self.create_mock_s3_bucket()

        pb, _ = self.publish_barrier(user=self.publisher)

        (data_file, metadata_file) = [
            VersionedFile(f) for f in list_s3_public_data_files()
        ]
        assert "v1.0.1" == data_file.version_label
        assert "v1.0.1" == metadata_file.version_label
