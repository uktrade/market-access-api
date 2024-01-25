import csv
from tempfile import NamedTemporaryFile
from typing import Dict, List

from celery import shared_task
from django.conf import settings
from notifications_python_client import NotificationsAPIClient

from api.barriers.csv import _transform_csv_row
from api.barriers.models import Barrier, BarrierSearchCSVDownloadEvent
from api.barriers.serializers import BarrierCsvExportSerializer
from api.documents.utils import get_bucket_name, get_s3_client_for_bucket


def upload_to_s3(filename: str, key: str) -> str:
    bucket_id = "default"
    bucket_name = get_bucket_name(bucket_id)
    s3_client = get_s3_client_for_bucket(bucket_id)
    s3_client.upload_file(filename, bucket_name, key)
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
    )


def write_to_temporary_file(
    temporary_file: NamedTemporaryFile,
    field_titles: Dict[str, str],
    serializer: BarrierCsvExportSerializer,
):
    writer = csv.DictWriter(
        temporary_file,
        extrasaction="ignore",
        fieldnames=field_titles.keys(),
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writerow(field_titles)
    for row in serializer.data:
        writer.writerow(_transform_csv_row(row))
    temporary_file.flush()


def create_named_temporary_file():
    return NamedTemporaryFile(mode="w+t", encoding="utf-8-sig")


def generate_and_upload_to_s3(
    s3_filename: str,
    field_titles: Dict[str, str],
    serializer: BarrierCsvExportSerializer,
) -> str:
    with create_named_temporary_file() as tf:
        write_to_temporary_file(tf, field_titles, serializer)
        presigned_url = upload_to_s3(tf.name, s3_filename)

    return presigned_url

@shared_task
def generate_s3_and_send_email(
    barrier_ids: List[str],
    s3_filename: str,
    email: str,
    first_name: str,
    field_titles: Dict[str, str],
) -> None:
    queryset = Barrier.objects.filter(id__in=barrier_ids)
    serializer = BarrierCsvExportSerializer(queryset, many=True)

    # save the download event in the database
    BarrierSearchCSVDownloadEvent.objects.create(
        email=email,
        barrier_ids=",".join(barrier_ids),
    )

    presigned_url = generate_and_upload_to_s3(s3_filename, field_titles, serializer)
    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    client.send_email_notification(
        email_address=email,
        template_id=settings.NOTIFY_GENERATED_FILE_ID,
        personalisation={
            "first_name": first_name.capitalize(),
            "file_name": s3_filename,
            "file_url": presigned_url,
        },
    )
