from rest_framework import serializers

from api.barriers.fields import BarrierReportStageListingField
from api.barriers.models import BarrierInstance
from api.metadata.serializers import BarrierTagSerializer
from api.metadata.utils import adjust_barrier_tags

# pylint: disable=R0201


class BarrierReportSerializer(serializers.ModelSerializer):
    progress = BarrierReportStageListingField(many=True, read_only=True)
    created_by = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    # TODO: deprecate this field (use summary instead)
    problem_description = serializers.CharField(source="summary", required=False)

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "problem_status",
            "status",
            "status_summary",
            "status_date",
            "sub_status",
            "sub_status_other",
            "export_country",
            "country_admin_areas",
            "sectors_affected",
            "all_sectors",
            "sectors",
            "product",
            "source",
            "other_source",
            "barrier_title",
            "problem_description",
            "summary",
            "is_summary_sensitive",
            "next_steps_summary",
            "progress",
            "created_by",
            "created_on",
            "modified_by",
            "modified_on",
            "tags",
            "trade_direction",
        )
        read_only_fields = (
            "id",
            "code",
            "progress",
            "created_by",
            "created_on",
            "modified_by",
            "modified_on",
        )

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}

    def get_tags(self, obj):
        tags = obj.tags.all()
        serializer = BarrierTagSerializer(tags, many=True)
        return serializer.data

    def validate_tags(self, tag_ids=None):
        if tag_ids is not None and type(tag_ids) is not list:
            raise serializers.ValidationError('Expected a list of tag IDs.')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Tags
        tag_ids = self.context["request"].data.get("tags")
        self.validate_tags(tag_ids)

        return attrs

    def save(self, *args, **kwargs):
        barrier = super().save(*args, **kwargs)
        # Tags
        tag_ids = self.initial_data.get("tags")
        adjust_barrier_tags(barrier, tag_ids)
