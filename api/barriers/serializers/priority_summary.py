from rest_framework import serializers

from api.barriers.models import Barrier, BarrierTopPrioritySummary
from api.barriers.serializers.progress_updates import UpdateSerializerMixin


class PrioritySummarySerializer(serializers.ModelSerializer, UpdateSerializerMixin):
    top_priority_summary_text = serializers.CharField(required=False)
    created_on = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    modified_on = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()
    barrier = serializers.CharField(source="barrier.id", required=False)

    class Meta:
        model = BarrierTopPrioritySummary
        fields = (
            "top_priority_summary_text",
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "barrier",
        )

    def create(self, validated_data):
        barrier = Barrier.objects.get(id=validated_data["barrier"]["id"])
        params = {
            **validated_data,
            "barrier": barrier,
        }
        return BarrierTopPrioritySummary.objects.create(**params)

    def update(self, instance, validated_data):
        instance.top_priority_summary_text = validated_data["top_priority_summary_text"]
        instance.save()
        return instance

    def get_created_by(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"

    def get_modified_by(self, obj):
        if obj.modified_by:
            return f"{obj.modified_by.first_name} {obj.modified_by.last_name}"

    def format_priority_summary_date(self, stored_date):
        formatted_date = stored_date.strftime("%d %B %Y")
        formatted_time = stored_date.strftime("%I:%M")
        am_pm = stored_date.strftime("%p").lower()
        timezone = stored_date.strftime("%Z")
        return f"{formatted_date} at {formatted_time}{am_pm} ({timezone})"

    def get_created_on(self, obj):
        if obj.created_on:
            return self.format_priority_summary_date(obj.created_on)

    def get_modified_on(self, obj):
        if obj.modified_on:
            return self.format_priority_summary_date(obj.modified_on)
