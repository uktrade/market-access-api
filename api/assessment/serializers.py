from rest_framework import serializers

from api.assessment.models import Assessment, ResolvabilityAssessment

from .fields import ImpactField


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


class ResolvabilityAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResolvabilityAssessment
        fields = (
            "id",
            "effort_to_resolve",
            "time_to_resolve",
            "explanation",
            "created_on",
            "created_by",
        )
        read_only_fields = ("id", "created_on", "created_by")


    def create(self, validated_data):
        validated_data["barrier_id"] = self.initial_data["barrier_id"]
        return super().create(validated_data)
