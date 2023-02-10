from rest_framework import serializers

from api.barriers.serializers.data_workspace import UserSerializer
from api.barriers.serializers.priority_summary import PrioritySummarySerializer
from api.metadata.constants import ECONOMIC_ASSESSMENT_IMPACT

from ...action_plans.serializers import ActionPlanSerializer
from .base import BarrierSerializerBase


class BarrierDetailSerializer(BarrierSerializerBase):
    action_plan = ActionPlanSerializer(required=False, many=False, allow_null=False)
    top_priority_summary = PrioritySummarySerializer(required=False, many=False)
    proposed_estimated_resolution_date_user = UserSerializer()

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
            "categories",
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
            "proposed_estimated_resolution_date",
            "proposed_estimated_resolution_date_user",
            "proposed_estimated_resolution_date_created",
            "estimated_resolution_date_change_reason",
            "id",
            "is_summary_sensitive",
            "is_top_priority",
            "last_seen_on",
            "location",
            "completion_percent",
            "modified_by",
            "modified_on",
            "other_source",
            "priority_level",
            "priority_summary",
            "product",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
            "public_eligibility_postponed",
            "reported_on",
            "resolvability_assessments",
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
            "top_priority_status",
            "top_priority_rejection_summary",
            "top_priority_summary",
        )


class BarrierMinimumDetailSerializer(BarrierSerializerBase):
    class Meta(BarrierSerializerBase.Meta):
        fields = ("id", "title")


class BarrierListSerializer(BarrierSerializerBase):
    # List Serializer provides list of fields returned to frontend
    # when loading/submitting on the search page

    current_valuation_assessment = serializers.SerializerMethodField()

    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "all_sectors",
            "archived",
            "archived_on",
            "caused_by_trading_bloc",
            "code",
            "country",
            "created_on",
            "id",
            "location",
            "modified_on",
            "reported_on",
            "sectors",
            "sectors_affected",
            "status",
            "status_date",
            "status_summary",
            "estimated_resolution_date",
            "tags",
            "title",
            "trade_direction",
            "trading_bloc",
            "progress_updates",
            "is_top_priority",
            "priority_level",
            "top_priority_status",
            "top_priority_rejection_summary",
            "current_valuation_assessment",
        )

    def get_current_valuation_assessment(self, obj):
        if obj.current_valuation_assessment:
            rating = ECONOMIC_ASSESSMENT_IMPACT[obj.current_valuation_assessment.impact]
            rating = rating.split(":")[1]
            return f"{rating}"
        else:
            return None
