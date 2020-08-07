import json

from celery import shared_task
from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.utils import timezone

from api.barriers.serializers.public_barriers import public_barriers_to_json
from api.core.utils import upload_to_s3


def latest_version():
    version = "v0.0.1"
    return version


def public_barrier_data_json_file_content():
    data = {"barriers": public_barriers_to_json()}
    return data


def metadata_json_file_content():
    data = {"release_date": str(timezone.now().date())}
    return data


@shared_task
def public_release_to_s3():
    """
    Generate a new JSON file and upload it to S3 along with metadata info.
    ** IMPORTANT ** These files are made available to the public via the gateway
    """
    version = latest_version()

    with NamedTemporaryFile(mode='w+t') as tf:
        json.dump(public_barrier_data_json_file_content(), tf, indent=4)
        tf.flush()
        s3_filename = f"{settings.PUBLIC_DATA_KEY_PREFIX}{version}/data.json"
        upload_to_s3(tf.name, settings.PUBLIC_DATA_BUCKET, s3_filename)

    with NamedTemporaryFile(mode='w+t') as tf:
        json.dump(metadata_json_file_content(), tf, indent=4)
        tf.flush()
        s3_filename = f"{settings.PUBLIC_DATA_KEY_PREFIX}{version}/metadata.json"
        upload_to_s3(tf.name, settings.PUBLIC_DATA_BUCKET, s3_filename)
