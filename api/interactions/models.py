from django.conf import settings
from django.db import models
from django.urls import reverse

from simple_history.models import HistoricalRecords

from api.metadata.constants import BARRIER_INTERACTION_TYPE
from api.core.models import ArchivableModel, BaseModel
from api.barriers.models import BarrierInstance
from api.documents.models import AbstractEntityDocumentModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Document(AbstractEntityDocumentModel):
    """ Document item related to interaction """

    size = models.IntegerField(null=True)
    mime_type = models.CharField(max_length=MAX_LENGTH, null=True)

    history = HistoricalRecords()

    @property
    def url(self):
        """Returns URL to download endpoint."""
        return reverse(
            "barrier-document-item-download", kwargs={"entity_document_pk": self.pk}
        )


class Interaction(BaseModel):
    """ Interaction records for each Barrier """

    barrier = models.ForeignKey(
        BarrierInstance, related_name="interactions_documents", on_delete=models.PROTECT
    )
    kind = models.CharField(choices=BARRIER_INTERACTION_TYPE, max_length=25)
    text = models.TextField(null=True)
    pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    documents = models.ManyToManyField(
        Document, related_name="documents", help_text="Interaction documents"
    )

    history = HistoricalRecords()

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)
