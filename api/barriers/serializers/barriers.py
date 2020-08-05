from rest_framework import serializers

from api.barriers.models import BarrierInstance
from .base import BarrierSerializerBase


class BarrierDetailSerializer(BarrierSerializerBase):
    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "assessment",
            "all_sectors",
            "archived",
            "archived_by",
            "archived_explanation",
            "archived_on",
            "archived_reason",
            "categories",
            "code",
            "commodities",
            "companies",
            "country",
            "created_by",
            "created_on",
            "end_date",
            "has_assessment",
            "id",
            "is_summary_sensitive",
            "last_seen_on",
            "modified_by",
            "modified_on",
            "other_source",
            "priority",
            "priority_summary",
            "product",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
            "sectors",
            "sectors_affected",
            "source",
            "status",
            "status_date",
            "status_summary",
            "sub_status",
            "sub_status_other",
            "summary",
            "tags",
            "term",
            "title",
            "trade_direction",
            "unarchived_by",
            "unarchived_on",
            "unarchived_reason",
            "wto_profile",
        )


class BarrierListSerializer(BarrierSerializerBase):
    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "all_sectors",
            "archived",
            "archived_on",
            "categories",
            "code",
            "country",
            "created_on",
            "id",
            "modified_on",
            "priority",
            "reported_on",
            "sectors",
            "sectors_affected",
            "status",
            "status_date",
            "status_summary",
            "tags",
            "title",
            "trade_direction",
        )


class BarrierResolveSerializer(serializers.ModelSerializer):
    """ Serializer for resolving a barrier """

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "status",
            "status_date",
            "status_summary",
            "created_on",
            "created_by",
        )
        read_only_fields = ("id", "status", "created_on", "created_by")


class BarrierStaticStatusSerializer(serializers.ModelSerializer):
    """ generic serializer for other barrier statuses """

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "status",
            "sub_status",
            "sub_status_other",
            "status_date",
            "status_summary",
            "created_on",
            "created_by",
        )
        read_only_fields = (
            "id",
            "status",
            "status_date",
            "is_active",
            "created_on",
            "created_by",
        )
