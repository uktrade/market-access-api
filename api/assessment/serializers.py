from rest_framework import serializers

from api.assessment.models import Assessment
from api.interactions.models import Document


class AssessmentSerializer(serializers.ModelSerializer):
    """ Serialzer for Barrier Assessment """

    created_by = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = (
            "id",
            "impact",
            "explanation",
            "value_to_economy",
            "import_market_size",
            "commercial_value",
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

    # def partial_update(self, instance, validated_data):
    #     instance.impact = validated_data.get("impact", instance.impact)
    #     instance.explanation = validated_data.get(
    #         "explanation",
    #         instance.explanation
    #     )
    #     instance.value_to_economy = validated_data.get(
    #         "value_to_economy",
    #         instance.value_to_economy
    #     )
    #     instance.import_market_size = validated_data.get(
    #         "import_market_size",
    #         instance.import_market_size
    #     )
    #     instance.import_market_size = validated_data.get(
    #         "commercial_value",
    #         instance.commercial_value
    #     )
    #     instance.modified_by = self.context["request"].user
    #     return instance

    def get_status(self, instance):
        """Get document status."""
        return instance.document.status


# class DocumentSerializer(serializers.ModelSerializer):
#     """Serializer for Document."""

#     status = serializers.SerializerMethodField()

#     class Meta:
#         model = AssessmentDocument
#         fields = ("id", "size", "mime_type", "original_filename", "url", "status")
#         read_only_fields = ("url", "created_by", "created_on", "status")

#     def create(self, validated_data):
#         """Create my entity document."""
#         doc = AssessmentDocument.objects.create(
#             original_filename=validated_data["original_filename"],
#             created_by=self.context["request"].user,
#         )

#         if "size" in validated_data:
#             doc.size = validated_data["size"]

#         if "mime_type" in validated_data:
#             doc.mime_type = validated_data["mime_type"]

#         doc.save()

#         return doc

#     def partial_update(self, instance, validated_data):
#         instance.original_filename = validated_data.get(
#             "original_filename", instance.original_filename
#         )
#         instance.size = validated_data.get("size", instance.size)
#         instance.mime_type = validated_data.get("mime_type", instance.mime_type)
#         instance.modified_by = self.context["request"].user
#         return instance

#     def get_status(self, instance):
#         """Get document status."""
#         return instance.document.status
