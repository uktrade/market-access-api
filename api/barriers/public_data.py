import json
import logging

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.utils import timezone

from api.barriers.serializers.public_barriers import public_barriers_to_json
from api.core.utils import upload_to_s3, list_s3_public_data_files

logger = logging.getLogger(__name__)


class VersionedFile:
    version_label = None
    major = 0
    minor = 0
    revision = 0

    def __init__(self, path):
        """
        :param path: STR - i.e: "market-access/v1.0.43/data.json"
        """
        self.path = path
        self.version_from_path()

    def version_from_path(self):
        """
        Helps to extract version number from a path
        :return: version label or None
        """
        try:
            self.version_label = self.path.split("/")[1]
            (self.major, self.minor, self.revision) = [
                int(s) for s in self.version_label.lstrip("v").split(".")
            ]
        except (IndexError, ValueError):
            return ""

    def next_revision(self, base=None):
        if isinstance(base, int):
            revision = base
        else:
            revision = self.revision
        return revision + 1

    @property
    def next_version(self):
        if (
            self.major == settings.PUBLIC_DATA_MAJOR
            and self.minor == settings.PUBLIC_DATA_MINOR
        ):
            revision = self.next_revision()
        else:
            revision = self.next_revision(0)
        return f"v{settings.PUBLIC_DATA_MAJOR}.{settings.PUBLIC_DATA_MINOR}.{revision}"

    @property
    def version_as_float(self):
        """
        To be able to compare file versions easily
        :return: FLOAT - i.e.: 10.12345
        """
        return float(f"{self.major}{self.minor}.{self.revision}")


def latest_file():
    version = 0
    latest_file = VersionedFile("")
    for path in list_s3_public_data_files():
        file = VersionedFile(path)
        if file.version_as_float > version:
            version = file.version_as_float
            latest_file = file
    return latest_file


def versioned_folder(version=None):
    """
    Helper to get full path of an S3 datafile object.
    :param version: STR - version folder of the file, defaults to latest version
    :return: STR - returns full path for the file
    """
    if not version:
        version = latest_file().version_label
    return f"{settings.PUBLIC_DATA_KEY_PREFIX}{version}"


def public_barrier_data_json_file_content(public_barriers=None):
    data = {"barriers": public_barriers_to_json(public_barriers)}
    return data


def metadata_json_file_content():
    data = {"release_date": str(timezone.now().date())}
    return data


def public_release_to_s3(public_barriers=None):
    """
    Generate a new JSON file and upload it to S3 along with metadata info.
    This file is designed to work with CITB public service,
    See more at - https://github.com/uktrade/market-access-public-frontend
    ** IMPORTANT **
    The S3 buckets are not exposed to the public.
    These files are actually made available to the public via DIT API Gateway.
    """
    if not settings.PUBLIC_DATA_TO_S3_ENABLED:
        logger.info(
            "Surfacing of public data to S3 is currently disabled. Please check app settings."
        )
        return

    # To make sure all files use the same version
    next_version = latest_file().next_version

    with NamedTemporaryFile(mode="w+t") as tf:
        json.dump(public_barrier_data_json_file_content(public_barriers), tf, indent=4)
        tf.flush()
        s3_filename = f"{versioned_folder(next_version)}/data.json"
        upload_to_s3(tf.name, settings.PUBLIC_DATA_BUCKET, s3_filename)

    with NamedTemporaryFile(mode="w+t") as tf:
        json.dump(metadata_json_file_content(), tf, indent=4)
        tf.flush()
        s3_filename = f"{versioned_folder(next_version)}/metadata.json"
        upload_to_s3(tf.name, settings.PUBLIC_DATA_BUCKET, s3_filename)
