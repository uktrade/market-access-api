from api.metadata.utils import (
    get_country,
    get_location_text,
    get_trading_bloc,
    get_trading_bloc_by_country_id,
)

from ...barriers.models import BarrierTopPrioritySummary
from .base import BaseHistoryItem


class BaseBarrierHistoryItem(BaseHistoryItem):
    model = "barrier"

    def get_barrier_id(self):
        return self.new_record.instance.id


class ArchivedHistoryItem(BaseBarrierHistoryItem):
    field = "archived"

    def get_value(self, record):
        if record.archived:
            return {
                "archived": True,
                "archived_reason": record.archived_reason,
                "archived_explanation": record.archived_explanation,
            }
        else:
            return {
                "archived": False,
                "unarchived_reason": record.unarchived_reason,
            }


class CategoriesHistoryItem(BaseBarrierHistoryItem):
    field = "categories"

    def get_value(self, record):
        return record.categories_cache or []


class CausedByTradingBlocHistoryItem(BaseBarrierHistoryItem):
    field = "caused_by_trading_bloc"

    def get_value(self, record):
        country_trading_bloc = None
        if record.country:
            country_trading_bloc = get_trading_bloc_by_country_id(str(record.country))
        return {
            "caused_by_trading_bloc": record.caused_by_trading_bloc,
            "country_trading_bloc": country_trading_bloc,
        }


class CommercialValueHistoryItem(BaseBarrierHistoryItem):
    field = "commercial_value"


class CommercialValueExplanationHistoryItem(BaseBarrierHistoryItem):
    field = "commercial_value_explanation"


class CommoditiesHistoryItem(BaseBarrierHistoryItem):
    field = "commodities"

    def get_value(self, record):
        for commodity in record.commodities_cache or []:
            if commodity.get("country"):
                commodity["country"] = get_country(commodity["country"].get("id"))
            elif commodity.get("trading_bloc"):
                commodity["trading_bloc"] = get_trading_bloc(
                    commodity["trading_bloc"].get("code")
                )
        return record.commodities_cache


class CompaniesHistoryItem(BaseBarrierHistoryItem):
    field = "companies"


class EconomicAssessmentEligibilityHistoryItem(BaseBarrierHistoryItem):
    field = "economic_assessment_eligibility"


class EconomicAssessmentEligibilitySummaryHistoryItem(BaseBarrierHistoryItem):
    field = "economic_assessment_eligibility_summary"


class EndDateHistoryItem(BaseBarrierHistoryItem):
    field = "estimated_resolution_date"


class IsSummarySensitiveHistoryItem(BaseBarrierHistoryItem):
    field = "is_summary_sensitive"


class LocationHistoryItem(BaseBarrierHistoryItem):
    field = "location"

    def get_value(self, record):
        return get_location_text(
            country_id=record.country,
            trading_bloc=record.trading_bloc,
            caused_by_trading_bloc=record.caused_by_trading_bloc,
            admin_area_ids=record.admin_areas,
        )


class PriorityHistoryItem(BaseBarrierHistoryItem):
    field = "priority"

    def get_value(self, record):
        priority = record.priority
        if priority is not None:
            priority = str(priority)
        return {
            "priority": priority,
            "priority_summary": record.priority_summary,
        }


class ProductHistoryItem(BaseBarrierHistoryItem):
    field = "product"


class PublicEligibilitySummaryHistoryItem(BaseBarrierHistoryItem):
    field = "public_eligibility_summary"


class SectorsHistoryItem(BaseBarrierHistoryItem):
    field = "sectors"

    def is_valid(self):
        if self.old_record or self.new_record:
            return True
        return False

    def get_value(self, record):
        return {
            "all_sectors": record.all_sectors,
            "sectors": [str(sector_id) for sector_id in record.sectors or []],
        }


class SourceHistoryItem(BaseBarrierHistoryItem):
    field = "source"

    def get_value(self, record):
        return {
            "source": record.source,
            "other_source": record.other_source,
        }


class StatusHistoryItem(BaseBarrierHistoryItem):
    field = "status"

    def get_value(self, record):
        return {
            "status": str(record.status),
            "status_date": record.status_date,
            "status_summary": record.status_summary,
            "sub_status": record.sub_status,
            "sub_status_other": record.sub_status_other,
        }


class SummaryHistoryItem(BaseBarrierHistoryItem):
    field = "summary"


class TagsHistoryItem(BaseBarrierHistoryItem):
    field = "tags"

    def get_value(self, record):
        return record.tags_cache or []


class TermHistoryItem(BaseBarrierHistoryItem):
    field = "term"


class TitleHistoryItem(BaseBarrierHistoryItem):
    field = "title"


class TradeCategoryHistoryItem(BaseBarrierHistoryItem):
    field = "trade_category"

    def get_value(self, record):
        if record.trade_category:
            return {
                "id": record.trade_category,
                "name": record.get_trade_category_display(),
            }


class TradeDirectionHistoryItem(BaseBarrierHistoryItem):
    field = "trade_direction"


class OrganisationsHistoryItem(BaseBarrierHistoryItem):
    field = "organisations"

    def get_value(self, record):
        return record.organisations_cache or []


class TopPriorityHistoryItem(BaseBarrierHistoryItem):
    field = "top_priority_status"

    def _get_top_priority_summary_text(self, record):
        """We want to get the top_priority_summary_text from the point in time when the change to the
        top_priority_status was made.
        """
        try:
            return (
                record.instance.top_priority_summary.first()
                .history.as_of(self.new_record.history_date)
                .top_priority_summary_text
            )
        # sometimes the BarrierTopPrioritySummary does not exist, at which point we return an empty string
        except (BarrierTopPrioritySummary.DoesNotExist, AttributeError):
            return ""

    def get_value(self, record):
        status = record.get_top_priority_status_display()
        if (
            record.top_priority_status == "APPROVED"
            or record.top_priority_status == "APPROVAL_PENDING"
            or record.top_priority_status == "REMOVAL_PENDING"
            or record.top_priority_status == "RESOLVED"
        ):
            # It's an accepted Top Priority Request, or pending review
            top_priority_reason = self._get_top_priority_summary_text(record)
        else:
            # The top_priority_status is NONE
            if record.top_priority_rejection_summary:
                # It's a rejected Top Priority Request
                status = "Rejected"
                top_priority_reason = record.top_priority_rejection_summary
            else:
                # The barrier has had its top-priority status removed
                status = "Removed"
                top_priority_reason = self._get_top_priority_summary_text(record)

        return {"value": status, "reason": top_priority_reason}


class TopPrioritySummaryHistoryItem(BaseHistoryItem):
    model = "barrier_top_priority_summary"
    field = "top_priority_summary_text"
