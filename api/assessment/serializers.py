from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.assessment.models import Assessment, ResolvabilityAssessment, StrategicAssessment
from api.barriers.fields import UserField
from api.core.serializers.fields import ApprovedField, ArchivedField
from api.core.serializers.mixins import CustomUpdateMixin

from .fields import (
    EffortToResolveField,
    ImpactField,
    StrategicAssessmentScaleField,
    TimeToResolveField,
)


class AssessmentSerializer(serializers.ModelSerializer):
    """ Serialzer for Barrier Assessment """

    created_by = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    impact = ImpactField(required=False)

    class Meta:
        model = Assessment
        fields = (
            "id",
            "impact",
            "explanation",
            "value_to_economy",
            "import_market_size",
            "commercial_value",
            "commercial_value_explanation",
            "export_value",
            "documents",
            "created_on",
            "created_by",
        )
        read_only_fields = ("id", "created_on", "created_by")

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}

    def get_documents(self, obj):
        if obj.documents is None:
            return None

        return [
            {
                "id": document.id,
                "name": document.original_filename,
                "size": document.size,
                "status": document.document.status,
            }
            for document in obj.documents.all()
        ]

    def get_status(self, instance):
        """Get document status."""
        return instance.document.status


class ResolvabilityAssessmentSerializer(CustomUpdateMixin, serializers.ModelSerializer):
    approved = ApprovedField(required=False)
    archived = ArchivedField(required=False)
    barrier_id = serializers.UUIDField()
    effort_to_resolve = EffortToResolveField()
    time_to_resolve = TimeToResolveField()
    archived_by = UserField(required=False)
    created_by = UserField(required=False)
    reviewed_by = UserField(required=False)

    class Meta:
        model = ResolvabilityAssessment
        fields = (
            "id",
            "approved",
            "archived",
            "archived_by",
            "archived_on",
            "barrier_id",
            "created_by",
            "created_on",
            "effort_to_resolve",
            "explanation",
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
            "reviewed_by",
            "reviewed_on",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user
        return super().create(validated_data)


class StrategicAssessmentSerializer(CustomUpdateMixin, serializers.ModelSerializer):
    approved = ApprovedField(required=False)
    archived = ArchivedField(required=False)
    barrier_id = serializers.UUIDField()
    scale = StrategicAssessmentScaleField()
    archived_by = UserField(required=False)
    created_by = UserField(required=False)
    reviewed_by = UserField(required=False)

    class Meta:
        model = StrategicAssessment
        fields = (
            "id",
            "approved",
            "archived",
            "archived_by",
            "archived_on",
            "barrier_id",
            "hmg_strategy",
            "government_policy",
            "trading_relations",
            "uk_interest_and_security",
            "uk_grants",
            "competition",
            "additional_information",
            "reviewed_by",
            "reviewed_on",
            "scale",
            "created_on",
            "created_by",
        )
        read_only_fields = ("id", "created_on", "created_by", "reviewed_by", "reviewed_on")

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user
        return super().create(validated_data)
