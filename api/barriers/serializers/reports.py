from api.barriers.fields import BarrierReportStageListingField

from .base import BarrierSerializerBase


class BarrierReportSerializer(BarrierSerializerBase):
    progress = BarrierReportStageListingField(many=True, read_only=True)

    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "all_sectors",
            "caused_by_trading_bloc",
            "code",
            "country",
            "created_by",
            "created_on",
            "id",
            "is_summary_sensitive",
            "is_top_priority",
            "location",
            "modified_by",
            "modified_on",
            "next_steps_summary",
            "other_source",
            "product",
            "progress",
            "public_eligibility",
            "public_eligibility_summary",
            "sectors",
            "main_sector",
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
            "trading_bloc",
            "commodities",
            "draft",
            "caused_by_admin_areas",
            "new_report_session_data",
            "companies",
            "related_organisations",
            "start_date",
            "is_start_date_known",
            "is_currently_active",
            "export_types",
            "export_description",
        )
