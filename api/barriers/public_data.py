import json
import logging

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.utils import timezone

from api.barriers.serializers.public_barriers import public_barriers_to_json
from api.core.utils import upload_to_s3


logger = logging.getLogger(__name__)


def latest_version():
    version = "v0.0.1"
    return version


def versioned_folder(version=latest_version()):
    return f"{settings.PUBLIC_DATA_KEY_PREFIX}{version}"


def public_barrier_data_json_file_content():
    data = {"barriers": public_barriers_to_json()}
    return data


def metadata_json_file_content():
    data = {"release_date": str(timezone.now().date())}
    return data


def public_release_to_s3():
    """
    Generate a new JSON file and upload it to S3 along with metadata info.
    This file is designed to work with CITB public service,
    See more at - https://github.com/uktrade/market-access-public-frontend
    ** IMPORTANT **
    The S3 buckets are not exposed to the public.
    These files are actually made available to the public via DIT API Gateway.
    """
    if not settings.PUBLIC_DATA_TO_S3_ENABLED:
        logger.info("Surfacing of public data to S3 is currently disabled. Please check app settings.")
        return

    with NamedTemporaryFile(mode='w+t') as tf:
        json.dump(public_barrier_data_json_file_content(), tf, indent=4)
        tf.flush()
        s3_filename = f"{versioned_folder()}/data.json"
        upload_to_s3(tf.name, settings.PUBLIC_DATA_BUCKET, s3_filename)

    with NamedTemporaryFile(mode='w+t') as tf:
        json.dump(metadata_json_file_content(), tf, indent=4)
        tf.flush()
        s3_filename = f"{versioned_folder()}/metadata.json"
        upload_to_s3(tf.name, settings.PUBLIC_DATA_BUCKET, s3_filename)
