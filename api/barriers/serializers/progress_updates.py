from rest_framework import serializers

from api.barriers.models import (
    Barrier,
    BarrierProgressUpdate,
    ProgrammeFundProgressUpdate,
)


class UpdateSerializerMixin:
    def get_created_by(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None

    def get_modified_by(self, obj):
        if obj.modified_by:
            return f"{obj.modified_by.first_name} {obj.modified_by.last_name}"
        return None


class ProgressUpdateSerializer(UpdateSerializerMixin, serializers.Serializer):
    from api.metadata.constants import PROGRESS_UPDATE_CHOICES

    status = serializers.ChoiceField(choices=PROGRESS_UPDATE_CHOICES)
    status_display = serializers.SerializerMethodField()
    message = serializers.CharField(source="update", required=False)
    next_steps = serializers.CharField(required=False)

    id = serializers.UUIDField(read_only=True)
    barrier = serializers.CharField(source="barrier.id")
    created_on = serializers.DateTimeField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    modified_by = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        barrier = Barrier.objects.get(id=validated_data["barrier"]["id"])
        params = {
            **validated_data,
            "barrier": barrier,
        }
        return BarrierProgressUpdate.objects.create(**params)

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.update = validated_data["update"]
        instance.next_steps = validated_data["next_steps"]
        instance.save()
        return instance

    def get_status_display(self, obj):
        return obj.get_status_display()

    class Meta:
        model = BarrierProgressUpdate
        fields = (
            "id",
            "barrier",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "status",
            "status_display",
            "message",
            "next_steps",
        )


class ProgrammeFundProgressUpdateSerializer(
    UpdateSerializerMixin, serializers.Serializer
):
    milestones_and_deliverables = serializers.CharField(required=False)
    expenditure = serializers.CharField(required=False)

    id = serializers.UUIDField(read_only=True)
    barrier = serializers.CharField(source="barrier.id")
    created_on = serializers.DateTimeField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    modified_by = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        barrier = Barrier.objects.get(id=validated_data["barrier"]["id"])
        params = {
            **validated_data,
            "barrier": barrier,
        }
        return ProgrammeFundProgressUpdate.objects.create(**params)

    def update(self, instance, validated_data):
        instance.milestones_and_deliverables = validated_data[
            "milestones_and_deliverables"
        ]
        instance.expenditure = validated_data["expenditure"]
        instance.save()
        return instance

    class Meta:
        model = ProgrammeFundProgressUpdate
        fields = (
            "id",
            "barrier",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "milestones_and_deliverables",
            "expenditure",
        )
