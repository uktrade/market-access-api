from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from simple_history.models import HistoricalRecords

from api.barriers.mixins import BarrierRelatedMixin
from api.core.models import ApprovalMixin, ArchivableMixin, BaseModel
from api.interactions.models import Document
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT,
    ECONOMIC_ASSESSMENT_RATING,
    RESOLVABILITY_ASSESSMENT_EFFORT,
    RESOLVABILITY_ASSESSMENT_TIME,
    STRATEGIC_ASSESSMENT_SCALE,
)

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class EconomicAssessmentHistoricalModel(models.Model):
    """
    Abstract model for history models tracking document changes.
    """
    documents_cache = ArrayField(
        models.JSONField(),
        blank=True,
        null=False,
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


class EconomicAssessment(ApprovalMixin, ArchivableMixin, BarrierRelatedMixin, BaseModel):
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="economic_assessments",
        on_delete=models.CASCADE,
    )
    analysis_data = models.TextField(blank=True)
    rating = models.CharField(choices=ECONOMIC_ASSESSMENT_RATING, max_length=25, blank=True)
    explanation = models.TextField(blank=True)
    ready_for_approval = models.BooleanField(default=False)
    documents = models.ManyToManyField(
        Document, related_name="assessment_documents", help_text="assessment documents"
    )
    import_market_size = models.BigIntegerField(blank=True, null=True)
    export_value = models.BigIntegerField(blank=True, null=True)

    # move to barrier?
    commercial_value = models.BigIntegerField(blank=True, null=True)
    commercial_value_explanation = models.TextField(blank=True)
    value_to_economy = models.BigIntegerField(blank=True, null=True)

    history = HistoricalRecords(bases=[EconomicAssessmentHistoricalModel])

    class Meta:
        ordering = ("-created_on", )
        permissions = (
            ("archive_economicassessment", "Can archive economic assessment"),
            ("approve_economicassessment", "Can approve economic assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for assessment in self.barrier.economic_assessments.filter(archived=False):
                assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)


class EconomicImpactAssessment(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    economic_assessment = models.ForeignKey(
        "assessment.EconomicAssessment",
        related_name="economic_impact_assessments",
        on_delete=models.CASCADE,
    )
    impact = models.CharField(choices=ECONOMIC_ASSESSMENT_IMPACT, max_length=25, blank=True)
    explanation = models.TextField(blank=True)

    history = HistoricalRecords()

    @property
    def barrier(self):
        return self.economic_assessment.barrier

    class Meta:
        ordering = ("-created_on", )
        permissions = (
            ("archive_economicimpactassessment", "Can archive economic impact assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for economic_assessment in self.economic_assessment.barrier.economic_assessments.all():
                for economic_impact_assessment in economic_assessment.economic_impact_assessments.filter(archived=False):
                    economic_impact_assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)


class ResolvabilityAssessment(ApprovalMixin, ArchivableMixin, BarrierRelatedMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="resolvability_assessments",
        on_delete=models.CASCADE,
    )
    time_to_resolve = models.PositiveIntegerField(choices=RESOLVABILITY_ASSESSMENT_TIME)
    effort_to_resolve = models.PositiveIntegerField(choices=RESOLVABILITY_ASSESSMENT_EFFORT)
    explanation = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_on", )
        permissions = (
            ("archive_resolvabilityassessment", "Can archive resolvability assessment"),
            ("approve_resolvabilityassessment", "Can approve resolvability assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for assessment in self.barrier.resolvability_assessments.filter(archived=False):
                assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)


class StrategicAssessment(ApprovalMixin, ArchivableMixin, BarrierRelatedMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="strategic_assessments",
        on_delete=models.CASCADE,
    )
    hmg_strategy = models.TextField()
    government_policy = models.TextField()
    trading_relations = models.TextField()
    uk_interest_and_security = models.TextField()
    uk_grants = models.TextField()
    competition = models.TextField()
    additional_information = models.TextField(blank=True)
    scale = models.PositiveIntegerField(choices=STRATEGIC_ASSESSMENT_SCALE)

    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_on", )
        permissions = (
            ("archive_strategicassessment", "Can archive strategic assessment"),
            ("approve_strategicassessment", "Can approve strategic assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for assessment in self.barrier.strategic_assessments.filter(archived=False):
                assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)
