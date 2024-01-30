import mock
import pytest
from django.conf import settings
from notifications_python_client import NotificationsAPIClient

from api.barrier_reports.serializers import BarrierCsvExportSerializer
from api.barrier_reports import service
from api.barriers.models import Barrier
from api.barrier_reports.models import BarrierReport, BarrierReportStatus
from api.barrier_reports.exceptions import BarrierReportNotificationError
from tests.barriers.factories import BarrierFactory
from mock import patch

pytestmark = [pytest.mark.django_db]


def test_serializer_to_csv_bytes():
    b1 = BarrierFactory()
    b2 = BarrierFactory()
    b3 = BarrierFactory()
    queryset = Barrier.objects.filter(id__in=[b1.id, b2.id])
    field_names = {
        "id": "id",
        "code": "code",
        "title": "Title",
        "status": "Status",
    }
    serializer = BarrierCsvExportSerializer(queryset, many=True)

    content = service.serializer_to_csv_bytes(serializer=serializer, field_names=field_names)

    assert content == (
        f'{",".join(field_names.values())}'
        f'\r\n{b2.id},{b2.code},{b2.title},{serializer.data[1]["status"]}'
        f'\r\n{b1.id},{b1.code},{b1.title},{serializer.data[0]["status"]}'
        f'\r\n'
    ).encode('utf-8')


@patch('api.barrier_reports.service.get_s3_client_and_bucket_name')
@patch('api.barrier_reports.service.serializer_to_csv_bytes')
@patch('api.barrier_reports.tasks.barrier_report_complete_notification')
def test_generate_barrier_report_file(mock_notify, mock_csv_bytes, mock_s3, user):
    b1 = BarrierFactory()
    b2 = BarrierFactory()

    barrier_report = BarrierReport.objects.create(
        user=user, status=BarrierReportStatus.PENDING, filename='test_file.csv'
    )
    s3_client, bucket = mock.Mock(), mock.Mock()
    mock_csv_bytes.return_value = b'test'
    mock_s3.return_value = s3_client, bucket

    service.generate_barrier_report_file(
        barrier_report_id=barrier_report.id,
        barrier_ids=[str(b1.id), str(b2.id)]
    )

    s3_client.put_object.assert_called_once_with(Bucket=bucket, Body=b'test', Key='test_file.csv')
    mock_notify.delay.assert_called_once_with(barrier_report_id=str(barrier_report.id))

    barrier_report.refresh_from_db()
    assert barrier_report.status == BarrierReportStatus.COMPLETE


def test_barrier_report_complete_notification_not_complete(user):
    barrier_report = BarrierReport.objects.create(
        user=user, status=BarrierReportStatus.PENDING, filename='test_file.csv'
    )

    with pytest.raises(BarrierReportNotificationError):
        service.barrier_report_complete_notification(barrier_report_id=barrier_report.id)


@patch.object(NotificationsAPIClient, 'send_email_notification')
@patch('api.barrier_reports.service.get_presigned_url')
def test_barrier_report_complete_notification_complete(mock_get_presigned_url, mock_notify_client, user):
    barrier_report = BarrierReport.objects.create(
        user=user, status=BarrierReportStatus.COMPLETE, filename='test_file.csv'
    )

    mock_get_presigned_url.return_value = 'test-url.com'

    service.barrier_report_complete_notification(barrier_report_id=barrier_report.id)

    mock_notify_client.assert_called_once_with(
        email_address='hey@siri.com',
        template_id=settings.NOTIFY_GENERATED_FILE_ID,
        personalisation={
            'first_name': user.first_name, 'file_name': barrier_report.filename, 'file_url': 'test-url.com'
        }
    )
