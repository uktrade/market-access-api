from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory, ReportFactory
from tests.metadata.factories import BarrierTagFactory


class TestBarrierTags(APITestMixin, TestCase):
    def test_get_barrier_without_tags(self):
        barrier = BarrierFactory()

        url = reverse("get-barrier", kwargs={"pk": barrier.id})
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == len(response.data["tags"])

    def test_get_barrier_with_tags(self):
        tag_title = "wobble"
        tag = BarrierTagFactory(title=tag_title)
        barrier = BarrierFactory(tags=(tag,))

        url = reverse("get-barrier", kwargs={"pk": barrier.id})
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == len(response.data["tags"])
        assert tag_title == response.data["tags"][0]["title"]

    def test_patch_barrier_with_valid_tags(self):
        barrier = BarrierFactory()
        tag_title = "wobble"
        tag = BarrierTagFactory(title=tag_title)

        assert not barrier.tags.exists(), "Expected no tags to start with."

        url = reverse("get-barrier", kwargs={"pk": barrier.id})
        payload = {"tags": [tag.id]}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        barrier.refresh_from_db()

        assert 1 == barrier.tags.count()
        assert tag.id == barrier.tags.first().id

    def test_patch_barrier_with_nonexisting_tags(self):
        barrier = BarrierFactory()

        assert not barrier.tags.exists(), "Expected no tags to start with."

        url = reverse("get-barrier", kwargs={"pk": barrier.id})
        payload = {"tags": [123321]}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        barrier.refresh_from_db()

        assert not barrier.tags.exists(), "Expected no tags to be assigned."

    def test_patch_barrier_swapping_tags(self):
        # existing tag
        tag01_title = "wobble"
        tag01 = BarrierTagFactory(title=tag01_title)
        barrier = BarrierFactory(tags=(tag01,))
        # the tag we want to switch to
        tag02_title = "wibble"
        tag02 = BarrierTagFactory(title=tag02_title)

        url = reverse("get-barrier", kwargs={"pk": barrier.id})

        assert (
            1 == barrier.tags.count()
        ), f"Expected only 1 tag, got {barrier.tags.count()}"
        assert tag01.id == barrier.tags.first().id

        payload = {"tags": [tag02.id]}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert (
            1 == barrier.tags.count()
        ), f"Expected only 1 tag, got {barrier.tags.count()}"
        assert tag02.id == barrier.tags.first().id

    def test_patch_barrier_extending_tags(self):
        # existing tag
        tag01_title = "wobble"
        tag01 = BarrierTagFactory(title=tag01_title)
        barrier = BarrierFactory(tags=(tag01,))
        # tag to be added
        tag02_title = "wibble"
        tag02 = BarrierTagFactory(title=tag02_title)

        url = reverse("get-barrier", kwargs={"pk": barrier.id})

        assert (
            1 == barrier.tags.count()
        ), f"Expected only 1 tag, got {barrier.tags.count()}"
        assert tag01.id == barrier.tags.first().id

        payload = {"tags": (tag01.id, tag02.id)}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert (
            2 == barrier.tags.count()
        ), f"Expected only 2 tags, got {barrier.tags.count()}"
        tag_ids = list(barrier.tags.values_list("id", flat=True))
        assert {tag01.id, tag02.id} == set(tag_ids)

    def test_patch_barrier_remove_all_tags(self):
        # existing tags
        tags = BarrierTagFactory.create_batch(2)
        barrier = BarrierFactory(tags=tags)
        url = reverse("get-barrier", kwargs={"pk": barrier.id})

        assert (
            2 == barrier.tags.count()
        ), f"Expected only 2 tags, got {barrier.tags.count()}"

        payload = {"tags": []}
        response = self.api_client.patch(url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        tags_count = barrier.tags.count()
        assert 0 == tags_count, f"Expected 0 tags, got {tags_count}."

    def test_patch_barrier_with_invalid_tags_returns_400(self):
        barrier = BarrierFactory()
        url = reverse("get-barrier", kwargs={"pk": barrier.id})

        assert not barrier.tags.exists(), "Expected no tags to start with."

        invalid_payloads = [123, "wobble", {"also": "invalid"}]
        for case in invalid_payloads:
            with self.subTest(case=case):
                payload = {"tags": case}
                response = self.api_client.patch(url, format="json", data=payload)

                assert status.HTTP_400_BAD_REQUEST == response.status_code
                barrier.refresh_from_db()
                assert not barrier.tags.exists(), "Expected no tags to be added."


class TestBarrierTagsFilter(APITestMixin, TestCase):
    def test_filter_barrier_tags__single_tag(self):
        tag = BarrierTagFactory()
        barrier = BarrierFactory(tags=(tag,))
        BarrierFactory()

        url = f'{reverse("list-barriers")}?tags={tag.id}'

        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier.id) == response.data["results"][0]["id"]

    def test_filter_barrier_tags__multiple_tags(self):
        tag1 = BarrierTagFactory()
        tag2 = BarrierTagFactory()
        barrier1 = BarrierFactory(tags=(tag1,))
        barrier2 = BarrierFactory(tags=(tag2,))
        BarrierFactory()

        url = f'{reverse("list-barriers")}?tags={tag1.id},{tag2.id}'

        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier1.id), str(barrier2.id)} == set(barrier_ids)

    def test_filter_barrier_tags__no_match(self):
        tag1 = BarrierTagFactory()
        BarrierFactory(tags=(tag1,))
        BarrierFactory()

        url = f'{reverse("list-barriers")}?tags=123,321'

        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]


class TestReportTags(APITestMixin, TestCase):
    def setUp(self):
        self.report = ReportFactory()
        self.url = reverse("get-report", kwargs={"pk": self.report.id})

    def test_get_report_without_tags(self):
        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == len(response.data["tags"])

    def test_get_report_with_tags(self):
        tag_title = "wobble"
        tag = BarrierTagFactory(title=tag_title)
        self.report.tags.add(tag)

        response = self.api_client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == len(response.data["tags"])
        assert tag_title == response.data["tags"][0]["title"]

    def test_patch_report_with_valid_tags(self):
        tag_title = "wobble"
        tag = BarrierTagFactory(title=tag_title)

        assert not self.report.tags.exists(), "Expected no tags to start with."

        payload = {"tags": [tag.id]}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.report.refresh_from_db()

        assert 1 == self.report.tags.count()
        assert tag.id == self.report.tags.first().id

    def test_patch_report_with_nonexisting_tags(self):
        assert not self.report.tags.exists(), "Expected no tags to start with."

        payload = {"tags": [123321]}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        self.report.refresh_from_db()

        assert not self.report.tags.exists(), "Expected no tags to be assigned."

    def test_patch_report_swapping_tags(self):
        # existing tag
        tag01_title = "wobble"
        tag01 = BarrierTagFactory(title=tag01_title)
        self.report.tags.add(tag01)
        # the tag we want to switch to
        tag02_title = "wibble"
        tag02 = BarrierTagFactory(title=tag02_title)

        assert (
            1 == self.report.tags.count()
        ), f"Expected only 1 tag, got {self.report.tags.count()}"
        assert tag01.id == self.report.tags.first().id

        payload = {"tags": [tag02.id]}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert (
            1 == self.report.tags.count()
        ), f"Expected only 1 tag, got {self.report.tags.count()}"
        assert tag02.id == self.report.tags.first().id

    def test_patch_report_extending_tags(self):
        # existing tag
        tag01_title = "wobble"
        tag01 = BarrierTagFactory(title=tag01_title)
        self.report.tags.add(tag01)
        # tag to be added
        tag02_title = "wibble"
        tag02 = BarrierTagFactory(title=tag02_title)

        assert (
            1 == self.report.tags.count()
        ), f"Expected only 1 tag, got {self.report.tags.count()}"
        assert tag01.id == self.report.tags.first().id

        payload = {"tags": (tag01.id, tag02.id)}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        assert (
            2 == self.report.tags.count()
        ), f"Expected only 2 tags, got {self.report.tags.count()}"
        tag_ids = list(self.report.tags.values_list("id", flat=True))
        assert {tag01.id, tag02.id} == set(tag_ids)

    def test_patch_report_remove_all_tags(self):
        # existing tags
        tags = BarrierTagFactory.create_batch(2)
        self.report.tags.add(*tags)

        assert (
            2 == self.report.tags.count()
        ), f"Expected only 2 tags, got {self.report.tags.count()}"

        payload = {"tags": []}
        response = self.api_client.patch(self.url, format="json", data=payload)

        assert status.HTTP_200_OK == response.status_code
        tags_count = self.report.tags.count()
        assert 0 == tags_count, f"Expected 0 tags, got {tags_count}."

    def test_patch_report_with_invalid_tags_returns_400(self):
        assert not self.report.tags.exists(), "Expected no tags to start with."

        invalid_payloads = [123, "wobble", {"also": "invalid"}]
        for case in invalid_payloads:
            with self.subTest(case=case):
                payload = {"tags": case}
                response = self.api_client.patch(self.url, format="json", data=payload)

                assert status.HTTP_400_BAD_REQUEST == response.status_code
                self.report.refresh_from_db()
                assert not self.report.tags.exists(), "Expected no tags to be added."
