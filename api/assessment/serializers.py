from django.core.cache import cache
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.fields import UserField
from api.barriers.models import Barrier
from api.core.serializers.fields import ApprovedField, ArchivedField
from api.core.serializers.mixins import AuditMixin, CustomUpdateMixin
from api.documents.fields import DocumentsField

from .automate.calculator import AssessmentCalculator
from .automate.exceptions import ComtradeError
from .fields import (
    EffortToResolveField,
    ImpactField,
    RatingField,
    StrategicAssessmentScaleField,
    TimeToResolveField,
)


class EconomicImpactAssessmentSerializer(AuditMixin, CustomUpdateMixin, serializers.ModelSerializer):
    archived = ArchivedField(required=False)
    archived_by = UserField(required=False)
    economic_assessment_id = serializers.IntegerField()
    impact = ImpactField()
    created_by = UserField(required=False)
    modified_by = UserField(required=False)

    class Meta:
        model = EconomicImpactAssessment
        fields = (
            "id",
            "archived",
            "archived_by",
            "archived_on",
            "created_by",
            "created_on",
            "modified_on",
            "modified_by",
            "economic_assessment_id",
            "impact",
            "explanation",
        )
        read_only_fields = (
            "id",
            "archived_by",
            "archived_on",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
        )


class EconomicAssessmentSerializer(AuditMixin, CustomUpdateMixin, serializers.ModelSerializer):
    approved = ApprovedField(required=False)
    archived = ArchivedField(required=False)
    archived_by = UserField(required=False)
    barrier_id = serializers.UUIDField()
    created_by = UserField(required=False)
    documents = DocumentsField(required=False)
    economic_impact_assessments = EconomicImpactAssessmentSerializer(required=False, many=True)
    modified_by = UserField(required=False)
    rating = RatingField(required=False)
    reviewed_by = UserField(required=False)

    class Meta:
        model = EconomicAssessment
        fields = (
            "id",
            "approved",
            "archived",
            "archived_by",
            "archived_on",
            "archived_reason",
            "automated_analysis_data",
            "barrier_id",
            "created_by",
            "created_on",
            "documents",
            "economic_impact_assessments",
            "explanation",
            "export_value",
            "import_market_size",
            "modified_on",
            "modified_by",
            "rating",
            "ready_for_approval",
            "reviewed_by",
            "reviewed_on",
            "value_to_economy",
        )
        read_only_fields = (
            "id",
            "archived_by",
            "archived_on",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "reviewed_by",
            "reviewed_on",
        )

    def create(self, validated_data):
        if self.initial_data.get("automate") is True:
            barrier = Barrier.objects.get(pk=validated_data["barrier_id"])
            assessment_calculator = AssessmentCalculator(cache=cache)
            commodity_codes = [c.trimmed_code for c in barrier.commodities.all()]
            try:
                data = assessment_calculator.calculate(
                    commodity_codes=commodity_codes,
                    product=barrier.product,
                    country1=barrier.country_name,
                )
            except ComtradeError as e:
                raise ValidationError(e)
            validated_data["automated_analysis_data"] = data

        return super().create(validated_data)


class ResolvabilityAssessmentSerializer(AuditMixin, CustomUpdateMixin, serializers.ModelSerializer):
    approved = ApprovedField(required=False)
    archived = ArchivedField(required=False)
    barrier_id = serializers.UUIDField()
    effort_to_resolve = EffortToResolveField()
    time_to_resolve = TimeToResolveField()
    archived_by = UserField(required=False)
    created_by = UserField(required=False)
    modified_by = UserField(required=False)
    reviewed_by = UserField(required=False)

    class Meta:
        model = ResolvabilityAssessment
        fields = (
            "id",
            "approved",
            "archived",
            "archived_by",
            "archived_on",
            "archived_reason",
            "barrier_id",
            "created_by",
            "created_on",
            "effort_to_resolve",
            "explanation",
            "modified_on",
            "modified_by",
            "reviewed_by",
            "reviewed_on",
            "time_to_resolve",
        )
        read_only_fields = (
            "id",
            "archived_by",
            "archived_on",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "reviewed_by",
            "reviewed_on",
        )


class StrategicAssessmentSerializer(AuditMixin, CustomUpdateMixin, serializers.ModelSerializer):
    approved = ApprovedField(required=False)
    archived = ArchivedField(required=False)
    barrier_id = serializers.UUIDField()
    scale = StrategicAssessmentScaleField()
    archived_by = UserField(required=False)
    created_by = UserField(required=False)
    modified_by = UserField(required=False)
    reviewed_by = UserField(required=False)

    class Meta:
        model = StrategicAssessment
        fields = (
            "id",
            "approved",
            "archived",
            "archived_by",
            "archived_on",
            "archived_reason",
            "barrier_id",
            "hmg_strategy",
            "government_policy",
            "trading_relations",
            "uk_interest_and_security",
            "uk_grants",
            "competition",
            "additional_information",
            "modified_on",
            "modified_by",
            "reviewed_by",
            "reviewed_on",
            "scale",
            "created_on",
            "created_by",
        )
        read_only_fields = (
            "id",
            "archived_by",
            "archived_on",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "reviewed_by",
            "reviewed_on",
        )
