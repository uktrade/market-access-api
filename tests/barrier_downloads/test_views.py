import json
from unittest import TestCase

import mock
from mock.mock import patch
from rest_framework import status
from rest_framework.reverse import reverse

from api.barrier_downloads.models import BarrierDownload
from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory


class TestBarrierDownloadViews(APITestMixin, TestCase):
    fixtures = ["users"]

    def setUp(self):
        super().setUp()

    def test_barrier_download_post_endpoint_no_results(self):
        url = reverse("barrier-downloads")

        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content == b'{"error": "No barriers matching filterset"}'

    def test_barrier_download_post_endpoint_no_results_filter(self):
        barrier = BarrierFactory()
        url = f'{reverse("barrier-downloads")}?text=wrong-{barrier.title}'

        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content == b'{"error": "No barriers matching filterset"}'

    @patch("api.barrier_downloads.service.get_s3_client_and_bucket_name")
    @patch("api.barrier_downloads.service.serializer_to_csv_bytes")
    @patch("api.barrier_downloads.tasks.barrier_download_complete_notification")
    def test_barrier_download_post_endpoint_success(self, mock_notify, mock_csv_bytes, mock_s3):
        assert BarrierDownload.objects.count() == 0

        barrier = BarrierFactory()
        url = reverse("barrier-downloads")

        response = self.api_client.post(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in data
        assert BarrierDownload.objects.count() == 1

        obj = BarrierDownload.objects.get(id=data["id"])

        # default filename
        assert obj.name == f"DMAS_{obj.created_on.strftime('%Y-%m-%d-%H-%M-%S')}.csv"

    @patch("api.barrier_downloads.tasks.generate_barrier_download_file")
    def test_barrier_download_post_endpoint_success_with_filter(self, mock_generate):
        barrier = BarrierFactory()
        url = f'{reverse("barrier-downloads")}?text={barrier.title}'

        response = self.api_client.post(
            url, data={"filters": {"text": barrier.title}}, format="json"
        )

        barrier_download = BarrierDownload.objects.get(
            id=json.loads(response.content)["id"]
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert barrier_download.filters == {"text": barrier.title}
        mock_generate.delay.assert_called_once_with(
            barrier_download_id=barrier_download.id,
            barrier_ids=[str(barrier.id)]
        )

    @mock.patch("api.barrier_downloads.views.service")
    def test_barrier_download_post_endpoint_success_and_retrieve(self, mock_service):
        barrier = BarrierFactory()
        barrier_download = BarrierDownload.objects.create(
            created_by=self.user, filters={}
        )
        mock_service.create_barrier_download.return_value = barrier_download
        url = reverse("barrier-downloads")

        response = self.api_client.post(url, kwargs={"hello": "WPR:D"})

        mock_service.create_barrier_download.assert_called_once_with(
            user=self.user, filters={}, barrier_ids=[str(barrier.id)]
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert str(barrier_download.id) == json.loads(response.content)["id"]

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert json.loads(response.content)["id"] == str(barrier_download.id)

    def test_get_barrier_download(self):
        barrier_download = BarrierDownload.objects.create(
            created_by=self.user, filters={}
        )

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data["id"] == str(barrier_download.id)

    def test_get_barrier_download_unauthorized(self):
        # Request made as self.user
        assert self.user != self.mock_user

        barrier_download = BarrierDownload.objects.create(
            created_by=self.mock_user, filters={}
        )

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert data == {"detail": "Unauthorized"}

    def test_barrier_download_list(self):
        assert self.user != self.mock_user

        barrier = BarrierFactory()
        br1 = BarrierDownload.objects.create(created_by=self.user, filters={})
        br2 = BarrierDownload.objects.create(created_by=self.user, filters={})

        # Won't show up
        br3 = BarrierDownload.objects.create(created_by=self.mock_user, filters={})

        url = reverse("barrier-downloads")

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data["count"] == 2
        assert data["results"][0]["id"] == str(br2.id)
        assert data["results"][1]["id"] == str(br1.id)

    @mock.patch("api.barrier_downloads.views.service")
    def test_get_presigned_url(self, mock_service):
        mock_service.get_presigned_url.return_value = "url.com"
        barrier_download = BarrierDownload.objects.create(
            created_by=self.user, filters={}
        )

        url = reverse(
            "get-barrier-download-presigned-url",
            kwargs={"pk": str(barrier_download.id)},
        )

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data == {"presigned_url": "url.com"}

    @mock.patch("api.barrier_downloads.views.service")
    def test_get_presigned_url_unauthorized(self, mock_service):
        mock_service.get_presigned_url.return_value = "url.com"
        barrier_download = BarrierDownload.objects.create(
            created_by=self.mock_user, filters={}
        )

        url = reverse(
            "get-barrier-download-presigned-url",
            kwargs={"pk": str(barrier_download.id)},
        )

        response = self.api_client.get(url)
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert data == {"detail": "Unauthorized"}

    def test_update_barrier_download_name(self):
        barrier_download = BarrierDownload.objects.create(
            created_by=self.user, filters={}
        )

        assert barrier_download.name is None

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.patch(url, data={"name": "New Name"})
        barrier_download.refresh_from_db()
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_200_OK
        assert data["id"] == str(barrier_download.id)
        assert data["name"] == "New Name"

    def test_update_barrier_download_name_unauthorized(self):
        barrier_download = BarrierDownload.objects.create(
            created_by=self.mock_user, filters={}
        )

        assert barrier_download.name is None

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.patch(url, data={"name": "New Name"})
        barrier_download.refresh_from_db()
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert data == {"detail": "Unauthorized"}

    def test_update_barrier_download_name_bad_request(self):
        barrier_download = BarrierDownload.objects.create(
            created_by=self.user, filters={}
        )

        assert barrier_download.name is None

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.patch(url, data={"bad_field": "hello"})
        barrier_download.refresh_from_db()
        data = json.loads(response.content)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert data == {"name": ["This field is required."]}

    @mock.patch("api.barrier_downloads.service.get_s3_client_and_bucket_name")
    def test_delete_barrier_download(self, mock_get_s3_client_and_bucket_name):
        s3_client, bucket = mock.Mock(), mock.Mock()
        mock_get_s3_client_and_bucket_name.return_value = s3_client, bucket
        barrier_download = BarrierDownload.objects.create(
            created_by=self.user, filters={}
        )

        assert barrier_download.name is None

        url = reverse("barrier-download", kwargs={"pk": str(barrier_download.id)})

        response = self.api_client.delete(url)

        assert BarrierDownload.objects.filter(id=barrier_download.id).count() == 0
        mock_get_s3_client_and_bucket_name.assert_called_once_with()
        assert response.status_code == status.HTTP_204_NO_CONTENT
