from rest_framework import serializers

from api.barriers.models import Barrier, BarrierTopPrioritySummary
from api.barriers.serializers.progress_updates import UpdateSerializerMixin


class PrioritySummarySerializer(serializers.ModelSerializer, UpdateSerializerMixin):
    top_priority_summary_text = serializers.CharField(required=False)
    created_on = serializers.SerializerMethodField(required=False)
    created_by = serializers.SerializerMethodField(required=False)
    modified_on = serializers.SerializerMethodField(required=False)
    modified_by = serializers.SerializerMethodField(required=False)
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
        if obj.created_by is not None:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        else:
            return None

    def get_modified_by(self, obj):
        if obj.modified_by is not None:
            return f"{obj.modified_by.first_name} {obj.modified_by.last_name}"
        else:
            return None

    def format_priority_summary_date(self, stored_date):
        if stored_date is not None:
            formatted_date = stored_date.strftime("%d %B %Y")
            formatted_time = stored_date.strftime("%I:%M")
            am_pm = stored_date.strftime("%p").lower()
            timezone = stored_date.strftime("%Z")
            return f"{formatted_date} at {formatted_time}{am_pm} ({timezone})"
        else:
            return None

    def get_created_on(self, obj):
        if obj.created_on is not None:
            return self.format_priority_summary_date(obj.created_on)
        else:
            return None

    def get_modified_on(self, obj):
        if obj.modified_on is not None:
            return self.format_priority_summary_date(obj.modified_on)
        else:
            return None
