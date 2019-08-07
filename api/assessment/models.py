from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse

from simple_history.models import HistoricalRecords

from api.metadata.constants import ASSESMENT_IMPACT
from api.core.models import ArchivableModel, BaseModel
from api.barriers.models import BarrierInstance
from api.documents.models import AbstractEntityDocumentModel
from api.interactions.models import Document

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


# class AssessmentDocument(AbstractEntityDocumentModel):
#     """ Document item related to assessment """

#     size = models.IntegerField(null=True)
#     mime_type = models.CharField(max_length=MAX_LENGTH, null=True)
#     detached = models.BooleanField(default=False)

#     history = HistoricalRecords()

#     @property
#     def url(self):
#         """Returns URL to download endpoint."""
#         return reverse(
#             "barrier-document-item-download", kwargs={"entity_document_pk": self.pk}
#         )


class AssessmentManager(models.Manager):
    """ Manage barrier assessment within the model, with archived not False """

    def get_queryset(self):
        return super(AssessmentManager, self).get_queryset().filter(Q(archived=False))


class Assessment(BaseModel, ArchivableModel):
    """ Assessment record for a Barrier """

    barrier = models.OneToOneField(
        BarrierInstance, on_delete=models.PROTECT
    )
    impact = models.CharField(choices=ASSESMENT_IMPACT, max_length=25)
    explanation = models.TextField()
    documents = models.ManyToManyField(
        Document, related_name="assessment_documents", help_text="assessment documents"
    )
    value_to_economy = models.BigIntegerField(null=True)
    import_market_size = models.BigIntegerField(null=True)
    commercial_value = models.BigIntegerField(null=True)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    objects = AssessmentManager()

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)
