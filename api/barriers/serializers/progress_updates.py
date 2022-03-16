from rest_framework import serializers

from api.barriers.models import Barrier, BarrierProgressUpdate


class ProgressUpdateSerializer(serializers.Serializer):
    from api.metadata.constants import PROGRESS_UPDATE_CHOICES

    id = serializers.UUIDField(read_only=True)
    barrier = serializers.CharField(source="barrier.id")
    created_on = serializers.DateTimeField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=PROGRESS_UPDATE_CHOICES)
    status_display = serializers.SerializerMethodField()
    message = serializers.CharField(source="update", required=False)
    next_steps = serializers.CharField(required=False)

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
            "modified_on",
            "status",
            "status_display" "message",
            "next_steps",
        )
