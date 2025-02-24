from rest_framework import serializers

from api.barriers.fields import SectorField, SectorsField, StatusField, TagsField
from api.barriers.serializers.priority_summary import PrioritySummarySerializer
from api.metadata.constants import ECONOMIC_ASSESSMENT_IMPACT
from .base import BarrierSerializerBase
from ...action_plans.serializers import ActionPlanSerializer


class BarrierDetailSerializer(BarrierSerializerBase):
    action_plan = ActionPlanSerializer(required=False, many=False, allow_null=False)
    top_priority_summary = PrioritySummarySerializer(required=False, many=False)

    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "action_plan",
            "admin_areas",
            "all_sectors",
            "archived",
            "archived_by",
            "archived_explanation",
            "archived_on",
            "archived_reason",
            "caused_by_trading_bloc",
            "code",
            "commercial_value",
            "commercial_value_explanation",
            "commodities",
            "companies",
            "country",
            "created_by",
            "created_on",
            "economic_assessment_eligibility",
            "economic_assessment_eligibility_summary",
            "economic_assessments",
            "valuation_assessments",
            "estimated_resolution_date",
            "estimated_resolution_date_change_reason",
            "id",
            "is_summary_sensitive",
            "is_top_priority",
            "last_seen_on",
            "location",
            "admin_areas",
            "completion_percent",
            "modified_by",
            "modified_on",
            "other_source",
            "policy_teams",
            "priority_level",
            "priority_summary",
            "product",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
            "public_eligibility_postponed",
            "reported_on",
            "resolvability_assessments",
            "main_sector",
            "sectors",
            "sectors_affected",
            "source",
            "status",
            "status_date",
            "status_summary",
            "strategic_assessments",
            "sub_status",
            "sub_status_other",
            "summary",
            "tags",
            "term",
            "title",
            "trade_category",
            "trade_direction",
            "trading_bloc",
            "unarchived_by",
            "unarchived_on",
            "unarchived_reason",
            "wto_profile",
            "government_organisations",
            "progress_updates",
            "programme_fund_progress_updates",
            "next_steps_items",
            "top_priority_status",
            "top_priority_rejection_summary",
            "top_priority_summary",
            "start_date",
            "export_types",
            "export_description",
            "is_currently_active",
            "related_organisations",
        )


class BarrierMinimumDetailSerializer(BarrierSerializerBase):
    class Meta(BarrierSerializerBase.Meta):
        fields = ("id", "title")


class BarrierListSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    archived = serializers.BooleanField(read_only=True)
    code = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    reported_on = serializers.DateTimeField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    archived_on = serializers.DateTimeField(read_only=True)
    status = StatusField(required=False)
    status_date = serializers.DateField(read_only=True)
    estimated_resolution_date = serializers.DateField(read_only=True)
    main_sector = SectorField(required=False)
    sectors = SectorsField(required=False)
    location = serializers.CharField(read_only=True)
    tags = TagsField(required=False)
    top_priority_status = serializers.CharField(read_only=True)
    priority_level = serializers.CharField(read_only=True)
    is_top_priority = serializers.BooleanField(read_only=True)
    current_valuation_assessment = serializers.SerializerMethodField()

    @staticmethod
    def get_current_valuation_assessment(instance):
        if instance.current_valuation_assessment:
            rating = ECONOMIC_ASSESSMENT_IMPACT[
                instance.current_valuation_assessment.impact
            ]
            rating = rating.split(":")[1]
            return f"{rating}"
        else:
            return None
