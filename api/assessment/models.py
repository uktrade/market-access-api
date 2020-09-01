from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from simple_history.models import HistoricalRecords

from api.barriers.mixins import BarrierRelatedMixin
from api.core.models import ArchivableMixin, BaseModel
from api.interactions.models import Document
from api.metadata.constants import ASSESMENT_IMPACT

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class AssessmentManager(models.Manager):
    """ Manage barrier assessment within the model, with archived not False """

    def get_queryset(self):
        return super(AssessmentManager, self).get_queryset().filter(Q(archived=False))


class AssessmentHistoricalModel(models.Model):
    """
    Abstract model for history models tracking document changes.
    """
    documents_cache = ArrayField(
        models.JSONField(),
        blank=True,
        null=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = self.diff_against(old_history).changed_fields

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


class Assessment(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    """ Assessment record for a Barrier """

    barrier = models.OneToOneField(
        "barriers.BarrierInstance", on_delete=models.CASCADE
    )
    impact = models.CharField(choices=ASSESMENT_IMPACT, max_length=25, null=True)
    explanation = models.TextField(null=True)
    documents = models.ManyToManyField(
        Document, related_name="assessment_documents", help_text="assessment documents"
    )
    value_to_economy = models.BigIntegerField(null=True)
    import_market_size = models.BigIntegerField(null=True)
    commercial_value = models.BigIntegerField(null=True)
    commercial_value_explanation = models.TextField(blank=True, default="")
    export_value = models.BigIntegerField(null=True)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords(bases=[AssessmentHistoricalModel])

    objects = AssessmentManager()

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)
