from rest_framework import serializers

from api.interactions.models import Document, Interaction, Mention, PublicBarrierNote
from api.user.serializers import UserMinimalDetailSerializer


class InteractionSerializer(serializers.ModelSerializer):
    """Serialzer for Barrier Ineractions"""

    created_by = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Interaction
        fields = (
            "id",
            "kind",
            "text",
            "pinned",
            "is_active",
            "documents",
            "created_on",
            "created_by",
            "barrier",
        )
        read_only_fields = ("barrier", "kind", "created_on", "created_by")

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


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document."""

    av_clean = serializers.SerializerMethodField()
    av_reason = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "size",
            "mime_type",
            "original_filename",
            "url",
            "status",
            "av_clean",
            "av_reason",
        )
        read_only_fields = (
            "url",
            "created_by",
            "created_on",
            "status",
            "av_clean",
            "av_reason",
        )

    def create(self, validated_data):
        """Create my entity document."""
        doc = Document.objects.create(
            original_filename=validated_data["original_filename"],
            created_by=self.context["request"].user,
        )

        if "size" in validated_data:
            doc.size = validated_data["size"]

        if "mime_type" in validated_data:
            doc.mime_type = validated_data["mime_type"]

        doc.save()

        return doc

    def partial_update(self, instance, validated_data):
        instance.original_filename = validated_data.get(
            "original_filename", instance.original_filename
        )
        instance.size = validated_data.get("size", instance.size)
        instance.mime_type = validated_data.get("mime_type", instance.mime_type)
        instance.modified_by = self.context["request"].user
        return instance

    def get_av_clean(self, instance):
        return instance.document.av_clean

    def get_av_reason(self, instance):
        return instance.document.av_reason

    def get_status(self, instance):
        """Get document status."""
        return instance.document.status


class PublicBarrierNoteSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    barrier = serializers.SerializerMethodField()

    class Meta:
        model = PublicBarrierNote
        fields = (
            "id",
            "text",
            "created_on",
            "created_by",
            "barrier",
        )
        read_only_fields = ("id", "created_on", "created_by")

    def get_created_by(self, obj):
        if obj.created_by is not None:
            return {"id": obj.created_by.id, "name": obj.created_user}

    def get_barrier(self, obj):
        if obj.public_barrier is not None:
            return obj.public_barrier.barrier.id


class MentionSerializer(serializers.ModelSerializer):

    message = serializers.SerializerMethodField()
    created_by = UserMinimalDetailSerializer(read_only=True)
    barrier = serializers.SerializerMethodField()
    go_to_url_path = serializers.SerializerMethodField()

    class Meta:
        model = Mention
        fields = (
            "id",
            "barrier",
            "email_used",
            "created_on",
            "created_by",
            "read_by_recipient",
            "message",
            "recipient",
            "text",
            "go_to_url_path",
        )

    def get_barrier(self, instance):
        from api.barriers.serializers.barriers import BarrierMinimumDetailSerializer

        return BarrierMinimumDetailSerializer(instance.barrier).data

    def get_message(self, instance):
        return instance.text

    def get_go_to_url_path(self, obj):
        if not obj.content_object:
            # Fallback in case there's no related note model
            return f"/barriers/{obj.barrier.id}/"
        return obj.content_object.get_note_url_path()


class ExcludeFromNotificationSerializer(serializers.Serializer):
    mention_notifications_enabled = serializers.BooleanField()
