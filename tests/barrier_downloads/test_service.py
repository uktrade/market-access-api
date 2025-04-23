import datetime

import mock
import pytest
from django.conf import settings
from mock import patch
from notifications_python_client import NotificationsAPIClient

import api.core.utils
from api.barrier_downloads import service
from api.barrier_downloads.exceptions import BarrierDownloadNotificationError
from api.barrier_downloads.models import BarrierDownload, BarrierDownloadStatus
from api.barrier_downloads.serializers import CsvDownloadSerializer
from api.barriers.models import Barrier, EstimatedResolutionDateRequest
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


def test_serializer_to_csv_bytes():
    b1 = BarrierFactory(estimated_resolution_date=datetime.datetime.now())
    b2 = BarrierFactory()
    erd = EstimatedResolutionDateRequest.objects.create(barrier=b1, reason="Reason")
    b3 = BarrierFactory()
    queryset = Barrier.objects.filter(id__in=[b1.id, b2.id])
    field_names = {
        "id": "id",
        "code": "code",
        "title": "Title",
        "status": "Status",
        "erd_request_status": "ERD Status",
        "erd_request_reason": "ERD Reason",
    }
    serializer = CsvDownloadSerializer(queryset, many=True)

    content = api.core.utils.serializer_to_csv_bytes(
        serializer=serializer, field_names=field_names
    )

    assert content == (
        f'{",".join(field_names.values())}'
        f'\r\n{b2.id},{b2.code},{b2.title},{serializer.data[1]["status"]},None,'
        f'\r\n{b1.id},{b1.code},{b1.title},{serializer.data[0]["status"]},Delete pending,{erd.reason}'
        f"\r\n"
    ).encode("utf-8")


@patch("api.barrier_downloads.service.get_s3_client_and_bucket_name")
@patch("api.barrier_downloads.service.serializer_to_csv_bytes")
@patch("api.barrier_downloads.tasks.barrier_download_complete_notification")
def test_generate_barrier_download_file(mock_notify, mock_csv_bytes, mock_s3, user):
    b1 = BarrierFactory()
    b2 = BarrierFactory()

    barrier_download = BarrierDownload.objects.create(
        created_by=user,
        status=BarrierDownloadStatus.PENDING,
        filters={},
        filename="test_file.csv",
    )
    s3_client, bucket = mock.Mock(), mock.Mock()
    mock_csv_bytes.return_value = b"test"
    mock_s3.return_value = s3_client, bucket

    service.generate_barrier_download_file(
        barrier_download_id=barrier_download.id, barrier_ids=[str(b1.id), str(b2.id)]
    )

    s3_client.put_object.assert_called_once_with(
        Bucket=bucket, Body=b"test", Key="test_file.csv"
    )
    mock_notify.delay.assert_called_once_with(
        barrier_download_id=str(barrier_download.id)
    )

    barrier_download.refresh_from_db()
    assert barrier_download.status == BarrierDownloadStatus.COMPLETE


@patch("api.barrier_downloads.service.serializer_to_csv_bytes", side_effect=Exception())
def test_generate_barrier_download_file_exception_handled(mock_csv_bytes, user):
    b1 = BarrierFactory()
    b2 = BarrierFactory()

    barrier_download = BarrierDownload.objects.create(
        created_by=user,
        status=BarrierDownloadStatus.PENDING,
        filters={},
        filename="test_file.csv",
    )

    with pytest.raises(Exception) as exc:
        service.generate_barrier_download_file(
            barrier_download_id=barrier_download.id,
            barrier_ids=[str(b1.id), str(b2.id)],
        )

    barrier_download.refresh_from_db()
    assert barrier_download.status == BarrierDownloadStatus.FAILED


def test_barrier_download_complete_notification_not_complete(user):
    barrier_download = BarrierDownload.objects.create(
        created_by=user,
        status=BarrierDownloadStatus.PENDING,
        filters={},
        filename="test_file.csv",
    )

    with pytest.raises(BarrierDownloadNotificationError):
        service.barrier_download_complete_notification(
            barrier_download_id=barrier_download.id
        )


@patch.object(NotificationsAPIClient, "send_email_notification")
@patch("api.barrier_downloads.service.get_presigned_url")
def test_barrier_download_complete_notification_complete(
    mock_get_presigned_url, mock_notify_client, user
):
    barrier_download = BarrierDownload.objects.create(
        created_by=user,
        status=BarrierDownloadStatus.COMPLETE,
        filters={},
        filename="test_file.csv",
    )

    mock_get_presigned_url.return_value = "test-url.com"

    service.barrier_download_complete_notification(
        barrier_download_id=barrier_download.id
    )

    mock_notify_client.assert_called_once_with(
        email_address="hey@siri.com",
        template_id=settings.NOTIFY_GENERATED_FILE_ID,
        personalisation={
            "first_name": user.first_name,
            "file_name": barrier_download.filename,
            "file_url": "test-url.com",
        },
    )
