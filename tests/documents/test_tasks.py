import pytest
from django.utils.timezone import now
import mock

from api.documents.tasks import delete_document

from .my_entity_document.models import MyEntityDocument

# mark the whole module for db use
pytestmark = pytest.mark.django_db



@mock.patch("api.documents.utils.get_bucket_name")
@mock.patch("api.documents.utils.get_s3_client_for_bucket")
def test_delete_document(mock_get_s3_client_for_bucket, mock_get_bucket_name):
    mock_get_s3_client_for_bucket.return_value = mock.Mock()
    mock_get_bucket_name.return_value = 'Test Name'

    """Tests if delete_document task deletes s3 document."""
    entity_document = MyEntityDocument.objects.create(
        original_filename="test.txt", my_field="lions"
    )
    document = entity_document.document
    document.uploaded_on = now()
    document.mark_deletion_pending()

    result = delete_document.apply(args=(document.pk,)).get()
    assert result is None

    with pytest.raises(MyEntityDocument.DoesNotExist):
        MyEntityDocument.objects.include_objects_deletion_pending().get(
            pk=entity_document.pk
        )


@mock.patch("api.documents.utils.get_bucket_name")
@mock.patch("api.documents.utils.get_s3_client_for_bucket")
def test_delete_document_s3_failure(mock_get_s3_client_for_bucket, mock_get_bucket_name):
    """
    Tests if delete_document task won't delete document from the
    database if deletion from S3 fails.
    """
    s3_client = mock.Mock()
    s3_client.delete_object.side_effect = Exception
    mock_get_s3_client_for_bucket.return_value = s3_client
    mock_get_bucket_name.return_value = 'Test Name'

    entity_document = MyEntityDocument.objects.create(
        original_filename="test.txt", my_field="lions"
    )
    document = entity_document.document
    document.uploaded_on = now()
    document.mark_deletion_pending()

    with pytest.raises(Exception):
        delete_document.apply(args=(document.pk,)).get()

    qs = MyEntityDocument.objects.include_objects_deletion_pending()
    assert qs.filter(pk=entity_document.pk).exists() is True
