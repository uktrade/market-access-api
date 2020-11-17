from rest_framework import serializers

from api.collaboration.models import TeamMember
from api.history.models import CachedHistoryItem
from api.metadata.constants import BarrierStatus
from .base import BarrierSerializerBase


class DataWorkspaceSerializer(BarrierSerializerBase):
    status_history = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()

    class Meta(BarrierSerializerBase.Meta):
        fields = (
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
            "commodities",
            "companies",
            "country",
            "created_by",
            "created_on",
            "economic_assessment_eligibility",
            "economic_assessment_eligibility_summary",
            "economic_assessments",
            "end_date",
            "id",
            "is_summary_sensitive",
            "modified_by",
            "modified_on",
            "other_source",
            "priority",
            "priority_summary",
            "product",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
            "resolvability_assessments",
            "sectors",
            "sectors_affected",
            "source",
            "status",
            "status_date",
            "status_history",
            "status_summary",
            "strategic_assessments",
            "sub_status",
            "sub_status_other",
            "summary",
            "tags",
            "team_count",
            "term",
            "title",
            "trade_category",
            "trade_direction",
            "trading_bloc",
            "unarchived_by",
            "unarchived_on",
            "unarchived_reason",
            "wto_profile",
        )

    def get_status_history(self, obj):
        history_items = CachedHistoryItem.objects.filter(
            barrier=obj,
            model="barrier",
            field="status",
        )
        status_lookup = dict(BarrierStatus.choices)
        return [
            {
                "date": item.date.isoformat(),
                "status": {
                    "id": item.new_record.status,
                    "name": status_lookup.get(item.new_record.status, "Unknown"),
                }
            } for item in history_items
        ]

    def get_team_count(self, obj):
        return TeamMember.objects.filter(barrier=obj).count()
