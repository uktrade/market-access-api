from http import HTTPStatus

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.helpers import get_or_create_public_barrier
from api.core.test_utils import APITestMixin
from api.interactions.models import ExcludeFromNotifcation, PublicBarrierNote
from tests.barriers.factories import BarrierFactory


class TestExcludeNotifcation(TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mentions-mark-as-read")
        self.user = User.objects.create_user("foo", "myemail@test.com", "bar")
        self.client.login(username="foo", password="bar")

    def test_exclude_notifcation(self):
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )

        res = self.client.post(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 1
        )

        # Show that repeated calls do not create repeated DB rows
        res = self.client.post(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 1
        )

    def test_remove_from_exclude_notification(self):
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )
        excluded = ExcludeFromNotifcation.objects.create(
            excluded_user=self.user,
            exclude_email=self.user.email,
            created_by=self.user,
            modified_by=self.user,
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is True
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 1
        )

        res = self.client.delete(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 0
        )

        # show that repeated calls to delete an exclusion does not cause an error
        res = self.client.delete(self.url)
        assert res.status_code == HTTPStatus.OK
        assert res.content == b"success"
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).exists()
            is False
        )
        assert (
            ExcludeFromNotifcation.objects.filter(excluded_user=self.user).count() == 0
        )


class PublicBarrierNoteTestCase(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory(priority="LOW")
        self.public_barrier, _created = get_or_create_public_barrier(self.barrier)
        self.note1 = PublicBarrierNote.objects.create(
            public_barrier=self.public_barrier, text="Note 1", created_by=self.mock_user
        )
        self.note2 = PublicBarrierNote.objects.create(
            public_barrier=self.public_barrier, text="Note 2", created_by=self.mock_user
        )

    def test_list_public_barrier_notes(self):
        url = reverse(
            "public-barrier-note-list", kwargs={"barrier_id": self.barrier.id}
        )
        response = self.api_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.data["count"] == 2
        note_ids = [result["id"] for result in response.data["results"]]
        assert self.note1.id in note_ids
        assert self.note2.id in note_ids

    def test_create_public_barrier_notes(self):
        url = reverse(
            "public-barrier-note-list", kwargs={"barrier_id": self.barrier.id}
        )
        response = self.api_client.post(url, data={"text": "New Note"})
        assert response.status_code == HTTPStatus.CREATED
        assert response.data["text"] == "New Note"

    def test_read_public_barrier_note(self):
        url = reverse("public-barrier-note-detail", kwargs={"pk": self.note1.id})
        response = self.api_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.data["id"] == self.note1.id

    def test_update_public_barrier_note(self):
        url = reverse("public-barrier-note-detail", kwargs={"pk": self.note1.id})
        response = self.api_client.patch(url, data={"text": "Updated Note"})
        assert response.status_code == HTTPStatus.OK
        assert response.data["text"] == "Updated Note"

    def test_delete_public_barrier_note(self):
        url = reverse("public-barrier-note-detail", kwargs={"pk": self.note1.id})
        response = self.api_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT
        self.note1.refresh_from_db()
        assert self.note1.archived is True
