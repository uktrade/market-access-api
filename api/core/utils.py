import operator
import os

import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings

from api.core.exceptions import S3UploadException


def is_copilot():
    return "COPILOT_ENVIRONMENT_NAME" in os.environ


def is_not_blank(s):
    return bool(s and s.strip())


def pretty_name(name):
    if is_not_blank(name):
        return " ".join(map(str, [x.capitalize() for x in name.split(".")]))
    return name


def cleansed_username(user):
    if user is not None:
        if is_not_blank(user.first_name) and is_not_blank(user.last_name):
            return pretty_name(f"{user.first_name}.{user.last_name}")

        if is_not_blank(user.username):
            if "@" in user.username:
                return pretty_name(user.username.split("@")[0])
            else:
                return pretty_name(user.username)

        if is_not_blank(user.email):
            return pretty_name(user.email.split("@")[0])

    return None


def nested_sort(obj):
    """
    Sort a dict/list and all it's values recursively
    """
    if isinstance(obj, dict):
        return sorted((k, nested_sort(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(nested_sort(x) for x in obj)
    else:
        return obj


def sort_list_of_dicts(obj, by_key, reverse=False):
    return sorted(obj, key=operator.itemgetter(by_key), reverse=reverse)


class EchoUTF8:
    """
    Writer that echoes written data and encodes to utf-8 if necessary.
    Used for streaming large CSV files, defined as per
    https://docs.djangoproject.com/en/2.0/howto/outputting-csv/.
    """

    def write(self, value):
        """Returns value that is being "written"."""
        if isinstance(value, str):
            return value.encode("utf-8")
        return value


def s3_client():
    if is_copilot():
        return boto3.client("s3")
    else:
        return boto3.client(
            "s3",
            aws_access_key_id=settings.PUBLIC_DATA_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.PUBLIC_DATA_AWS_SECRET_ACCESS_KEY,
        )


def upload_to_s3(local_file, bucket, s3_file=None):
    s3 = s3_client()
    s3_file = s3_file or local_file
    try:
        s3.upload_file(local_file, bucket, s3_file)
    except (FileNotFoundError, NoCredentialsError) as e:
        raise S3UploadException(e)


def read_file_from_s3(filename):
    s3 = s3_resource()
    return s3.Object(settings.PUBLIC_DATA_BUCKET, filename)


def s3_resource():
    if is_copilot():
        return boto3.resource("s3")
    else:
        return boto3.resource(
            "s3",
            region_name=settings.PUBLIC_DATA_BUCKET_REGION,
            aws_access_key_id=settings.PUBLIC_DATA_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.PUBLIC_DATA_AWS_SECRET_ACCESS_KEY,
        )


def list_s3_public_data_files(client=None):
    if not client:
        client = s3_client()
    """
    list files in specific S3 URL
    :returns: generator
    """
    response = client.list_objects(
        Bucket=settings.PUBLIC_DATA_BUCKET, Prefix=settings.PUBLIC_DATA_KEY_PREFIX
    )
    for content in response.get("Contents", []):
        yield content.get("Key")
