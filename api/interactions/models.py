from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.urls import reverse
from simple_history.models import HistoricalRecords

from api.barriers.mixins import BarrierRelatedMixin
from api.core.models import ArchivableMixin, BaseModel
from api.documents.models import AbstractEntityDocumentModel
from api.metadata.constants import BARRIER_INTERACTION_TYPE

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Document(AbstractEntityDocumentModel):
    """ Document item related to interaction """

    size = models.IntegerField(null=True)
    mime_type = models.CharField(max_length=MAX_LENGTH, blank=True)
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
        models.JSONField(),
        blank=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = self.diff_against(old_history).changed_fields

        if "archived" in changed_fields:
            if self.documents_cache:
                return ["text", "documents"]
            return ["text"]

        if "documents" in changed_fields:
            changed_fields.remove("documents")

        new_document_ids = [doc["id"] for doc in self.documents_cache or []]
        old_document_ids = [doc["id"] for doc in old_history.documents_cache or []]
        if set(new_document_ids) != set(old_document_ids):
            changed_fields.append("documents")

        return changed_fields

    def update_documents(self):
        self.documents_cache = [
            {
                "id": str(document["id"]),
                "name": document["original_filename"],
            } for document in self.instance.documents.values("id", "original_filename")
        ]

    def save(self, *args, **kwargs):
        self.update_documents()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Interaction(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    """ Interaction records for each Barrier """

    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="interactions_documents",
        on_delete=models.CASCADE,
    )
    kind = models.CharField(choices=BARRIER_INTERACTION_TYPE, max_length=25)
    text = models.TextField(blank=True)
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


class PublicBarrierNote(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    public_barrier = models.ForeignKey(
        "barriers.PublicBarrier",
        related_name="notes",
        on_delete=models.CASCADE,
    )
    text = models.TextField()

    history = HistoricalRecords()

    @property
    def barrier(self):
        return self.public_barrier.barrier

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)
