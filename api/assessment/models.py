from typing import List, Optional
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from simple_history.models import HistoricalRecords

from api.assessment.constants import PRELIMINARY_ASSESSMENT_CHOICES
from api.barriers.mixins import BarrierRelatedMixin
from api.core.models import ApprovalMixin, ArchivableMixin, BaseModel
from api.history.v2.service import get_model_history
from api.interactions.models import Document
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT,
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS,
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC,
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
            }
            for document in self.instance.documents.values("id", "original_filename")
        ]

    def save(self, *args, **kwargs):
        self.update_documents()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class EconomicAssessment(
    ApprovalMixin, ArchivableMixin, BarrierRelatedMixin, BaseModel
):
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="economic_assessments",
        on_delete=models.CASCADE,
    )
    automated_analysis_data = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True
    )
    rating = models.CharField(
        choices=ECONOMIC_ASSESSMENT_RATING, max_length=25, blank=True
    )
    explanation = models.TextField(blank=True)
    ready_for_approval = models.BooleanField(default=False)

    @property
    def export_potential(self):
        if self.automated_analysis_data:
            return self.automated_analysis_data.get("export_potential", {})
        else:
            return {}

    @property
    def latest_valuation_assessment(self):
        return self.economic_impact_assessments.all().order_by("created_on").first()

    # import_market_size, export_value, value_to_economy and documents are now deprecated,
    # - leaving the fields here to preserve the data and history
    import_market_size = models.BigIntegerField(blank=True, null=True)
    export_value = models.BigIntegerField(blank=True, null=True)
    value_to_economy = models.BigIntegerField(blank=True, null=True)
    documents = models.ManyToManyField(Document, related_name="economic_assessments")

    history = HistoricalRecords(bases=[EconomicAssessmentHistoricalModel])

    class Meta:
        ordering = ("-created_on",)
        permissions = (
            ("archive_economicassessment", "Can archive economic assessment"),
            ("approve_economicassessment", "Can approve economic assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for assessment in self.barrier.economic_assessments.filter(archived=False):
                assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)

    @classmethod
    def get_history(cls, barrier_id: str, fields: Optional[List] = None):
        qs = cls.history.filter(barrier__id=barrier_id)
        default_fields = (
            "approved",
            "archived",
            "documents_cache",
            "explanation",
            "export_value",
            "import_market_size",
            "rating",
            "ready_for_approval",
            "value_to_economy",
        )
        if fields is None:
            fields = default_fields

        return get_model_history(
            qs,
            model="economic_assessment",
            fields=fields,
            track_first_item=True,
        )


class EconomicImpactAssessment(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    """
    Analysts requested the name to be changed to Valuation Assessment
     - it reflects more what the numbers mean

    When created an Impact Assessment will belong to a barriers current economic assessment,
    otherwise it'll belong to the barrier alone.
    This is to preserve previous data and also old behaviour while removing strict dependence
    on the economic assessment.
    """

    id = models.UUIDField(primary_key=True, default=uuid4)
    economic_assessment = models.ForeignKey(
        "assessment.EconomicAssessment",
        related_name="economic_impact_assessments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="valuation_assessments",
        on_delete=models.CASCADE,
        null=True,
    )
    impact = models.PositiveIntegerField(choices=ECONOMIC_ASSESSMENT_IMPACT)
    explanation = models.TextField(blank=True)

    history = HistoricalRecords()

    @property
    def rating(self):
        rating = ""
        if self.impact:
            rating = ECONOMIC_ASSESSMENT_IMPACT[self.impact]
        return rating

    @property
    def midpoint(self):
        midpoint = ""
        if self.impact:
            midpoint = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS[self.impact]
        return midpoint

    @property
    def midpoint_value(self):
        value = ""
        if self.midpoint:
            value = ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC[self.midpoint]
        return value

    class Meta:
        ordering = ("-created_on",)
        permissions = (
            (
                "archive_economicimpactassessment",
                "Can archive economic impact assessment",
            ),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.economic_assessment:
                for (
                    economic_assessment
                ) in self.economic_assessment.barrier.economic_assessments.all():
                    for (
                        economic_impact_assessment
                    ) in economic_assessment.economic_impact_assessments.filter(
                        archived=False
                    ):
                        economic_impact_assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)

    @classmethod
    def get_history(cls, barrier_id: str, fields: Optional[List] = None):
        qs = cls.history.filter(economic_assessment__barrier_id=barrier_id)
        default_fields = (
            "archived",
            "explanation",
            "impact",
        )
        if fields is None:
            fields = default_fields

        return get_model_history(
            qs,
            model="economic_impact_assessment",
            fields=fields,
            track_first_item=True,
        )


class ResolvabilityAssessment(
    ApprovalMixin, ArchivableMixin, BarrierRelatedMixin, BaseModel
):
    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="resolvability_assessments",
        on_delete=models.CASCADE,
    )
    time_to_resolve = models.PositiveIntegerField(choices=RESOLVABILITY_ASSESSMENT_TIME)
    effort_to_resolve = models.PositiveIntegerField(
        choices=RESOLVABILITY_ASSESSMENT_EFFORT
    )
    explanation = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_on",)
        permissions = (
            ("archive_resolvabilityassessment", "Can archive resolvability assessment"),
            ("approve_resolvabilityassessment", "Can approve resolvability assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for assessment in self.barrier.resolvability_assessments.filter(
                archived=False
            ):
                assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)

    @classmethod
    def get_history(cls, barrier_id: str, fields: Optional[List] = None):
        qs = cls.history.filter(barrier_id=barrier_id)
        default_fields = (
            "approved",
            "archived",
            "effort_to_resolve",
            "explanation",
            "time_to_resolve",
        )
        if fields is None:
            fields = default_fields

        return get_model_history(
            qs,
            model="resolvability_assessment",
            fields=fields,
            track_first_item=True,
        )


class StrategicAssessment(
    ApprovalMixin, ArchivableMixin, BarrierRelatedMixin, BaseModel
):
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
        ordering = ("-created_on",)
        permissions = (
            ("archive_strategicassessment", "Can archive strategic assessment"),
            ("approve_strategicassessment", "Can approve strategic assessment"),
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            for assessment in self.barrier.strategic_assessments.filter(archived=False):
                assessment.archive(user=self.created_by)
        super().save(*args, **kwargs)

    @classmethod
    def get_history(cls, barrier_id: str, fields: Optional[List] = None):
        qs = cls.history.filter(barrier_id=barrier_id)
        default_fields = (
            "approved",
            "archived",
            "hmg_strategy",
            "government_policy",
            "trading_relations",
            "uk_interest_and_security",
            "uk_grants",
            "competition",
            "additional_information",
            "scale",
        )
        if fields is None:
            fields = default_fields

        return get_model_history(
            qs,
            model="strategic_assessment",
            fields=fields,
            track_first_item=True,
        )


class PreliminaryAssessment(BarrierRelatedMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.OneToOneField(
        "barriers.Barrier",
        related_name="preliminary_assessment",
        on_delete=models.CASCADE,
    )
    value = models.PositiveIntegerField(choices=PRELIMINARY_ASSESSMENT_CHOICES)
    details = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_on",)

    @classmethod
    def get_history(cls, barrier_id: str, fields: Optional[List] = None):
        qs = cls.history.filter(barrier__id=barrier_id)

        if not fields:
            fields = ("value", "details")

        return get_model_history(
            qs,
            model="preliminary_assessment",
            fields=fields,
            track_first_item=True,
        )
