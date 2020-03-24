from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Q
from django.urls import reverse

from simple_history.models import HistoricalRecords

from api.metadata.constants import BARRIER_INTERACTION_TYPE
from api.core.models import ArchivableModel, BaseModel
from api.barriers.models import BarrierInstance
from api.documents.models import AbstractEntityDocumentModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Document(AbstractEntityDocumentModel, ArchivableModel):
    """ Document item related to interaction """

    size = models.IntegerField(null=True)
    mime_type = models.CharField(max_length=MAX_LENGTH, null=True)
    detached = models.BooleanField(default=False)

    history = HistoricalRecords()

    @property
    def url(self):
        """Returns URL to download endpoint."""
        return reverse(
            "barrier-document-item-download", kwargs={"entity_document_pk": self.pk}
        )


class InteractionManager(models.Manager):
    """ Manage barrier interactions within the model, with archived not False """

    def get_queryset(self):
        return super(InteractionManager, self).get_queryset().filter(Q(archived=False))


class InteractionHistoricalModel(models.Model):
    """
    Abstract model for history models tracking document changes.
    """
    documents_cache = ArrayField(
        JSONField(),
        blank=True,
        null=True,
        default=None,
    )

    def get_changed_fields(self, old_history):
        changed_fields = self.diff_against(old_history).changed_fields

        if self.documents_cache != old_history.documents_cache:
            changed_fields.append("documents")

        return changed_fields

    def update_documents(self):
        self.documents_cache = [
            {
                "id": str(document["id"]),
                "name": document["original_filename"],
            } for document in instance.documents.values("id", "original_filename")
        ]

    def save(self, *args, **kwargs):
        self.update_documents()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Interaction(BaseModel, ArchivableModel):
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

    history = HistoricalRecords(bases=[InteractionHistoricalModel])

    objects = InteractionManager()

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)
