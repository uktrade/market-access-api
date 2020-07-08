from http import HTTPStatus

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.models import PublicBarrier
from api.core.test_utils import APITestMixin
from api.interactions.models import PublicBarrierNote

from tests.barriers.factories import BarrierFactory


class PublicBarrierNoteTestCase(APITestMixin, APITestCase):

    def setUp(self):
        self.barrier = BarrierFactory(priority="LOW")
        self.public_barrier, created = PublicBarrier.objects.get_or_create(
            barrier=self.barrier,
            defaults={
                "status": self.barrier.status,
                "country": self.barrier.export_country,
                "sectors": self.barrier.sectors,
                "all_sectors": self.barrier.all_sectors,
            }
        )
        self.note1 = PublicBarrierNote.objects.create(
            public_barrier=self.public_barrier,
            text="Note 1"
        )
        self.note2 = PublicBarrierNote.objects.create(
            public_barrier=self.public_barrier,
            text="Note 2"
        )

    def test_list_public_barrier_notes(self):
        url = reverse("public-barrier-note-list", kwargs={"barrier_id": self.barrier.id})
        response = self.api_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.data["count"] == 2
        note_ids = [result["id"] for result in response.data["results"]]
        assert self.note1.id in note_ids
        assert self.note2.id in note_ids

    def test_create_public_barrier_notes(self):
        url = reverse("public-barrier-note-list", kwargs={"barrier_id": self.barrier.id})
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
