import uuid

import factory
from django.utils.timezone import utc

from api.core.test_utils import create_test_user
from api.documents.models import UPLOAD_STATUSES


class DocumentFactory(factory.django.DjangoModelFactory):
    """Document factory."""
    # a_user = create_test_user(
    #     first_name="",
    #     last_name="",
    #     email="Testo@Useri.com",
    #     username="",
    # )

    id = factory.LazyFunction(uuid.uuid4)
    created_by = None
    modified_by = None
    bucket_id = 'default'
    path = factory.Sequence(lambda n: f'projects/doc{n}.txt')
    uploaded_on = factory.Faker('past_datetime', tzinfo=utc)
    scan_initiated_on = None
    scanned_on = None
    av_clean = None
    av_reason = ''
    status = UPLOAD_STATUSES.not_virus_scanned

    class Meta:
        model = 'documents.Document'
