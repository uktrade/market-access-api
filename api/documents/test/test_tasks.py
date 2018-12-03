import pytest
from django.utils.timezone import now

from api.documents.tasks import delete_document
from api.documents.test.my_entity_document.models import MyEntityDocument
from api.documents.utils import get_bucket_name

from api.documents.utils import get_s3_client_for_bucket
from botocore.stub import Stubber


# mark the whole module for db use
pytestmark = pytest.mark.django_db


@pytest.fixture()
def s3_stubber():
    """S3 stubber using the botocore Stubber class."""
    s3_client = get_s3_client_for_bucket("default")
    with Stubber(s3_client) as s3_stubber:
        yield s3_stubber


def test_delete_document(s3_stubber):
    """Tests if delete_document task deletes s3 document."""
    entity_document = MyEntityDocument.objects.create(
        original_filename="test.txt", my_field="lions"
    )
    document = entity_document.document
    document.uploaded_on = now()
    document.mark_deletion_pending()

    bucket_name = get_bucket_name(document.bucket_id)

    s3_stubber.add_response(
        "delete_object",
        {"ResponseMetadata": {"HTTPStatusCode": 204}},
        expected_params={"Bucket": bucket_name, "Key": document.path},
    )

    result = delete_document.apply(args=(document.pk,)).get()
    assert result is None

    with pytest.raises(MyEntityDocument.DoesNotExist):
        MyEntityDocument.objects.include_objects_deletion_pending().get(
            pk=entity_document.pk
        )


def test_delete_document_s3_failure(s3_stubber):
    """
    Tests if delete_document task won't delete document from the
    database if deletion from S3 fails.
    """
    entity_document = MyEntityDocument.objects.create(
        original_filename="test.txt", my_field="lions"
    )
    document = entity_document.document
    document.uploaded_on = now()
    document.mark_deletion_pending()

    bucket_name = get_bucket_name(document.bucket_id)

    s3_stubber.add_client_error(
        "delete_object",
        service_error_code=500,
        expected_params={"Bucket": bucket_name, "Key": document.path},
    )

    with pytest.raises(Exception):
        delete_document.apply(args=(document.pk,)).get()

    qs = MyEntityDocument.objects.include_objects_deletion_pending()
    assert qs.filter(pk=entity_document.pk).exists() is True
