from api.barriers.models import BarrierInstance
from .base import BaseHistoryItem, HistoryItemFactory


class BaseBarrierHistoryItem(BaseHistoryItem):
    model = "barrier"


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


class CompaniesHistoryItem(BaseBarrierHistoryItem):
    field = "companies"


class IsSummarySensitiveHistoryItem(BaseBarrierHistoryItem):
    field = "is_summary_sensitive"


class LocationHistoryItem(BaseBarrierHistoryItem):
    field = "location"

    def get_value(self, record):
        return {
            "country": str(record.export_country),
            "admin_areas":  [
                str(admin_area) for admin_area in record.country_admin_areas or []
            ],
        }


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


class ScopeHistoryItem(BaseBarrierHistoryItem):
    field = "problem_status"


class SectorsHistoryItem(BaseBarrierHistoryItem):
    field = "sectors"

    def get_data(self):
        if self.old_record or self.new_record:
            return super().get_data()

    def get_value(self, record):
        return [str(sector_id) for sector_id in record.sectors or []]


class SourceHistoryItem(BaseBarrierHistoryItem):
    field = "source"

    def get_value(self, record):
        return {
            "source": record.source,
            "other_source": record.other_source,
        }


class StatusHistoryItem(BaseBarrierHistoryItem):
    field = "status"

    def get_data(self):
        if not (self.old_record.status == 0 and self.new_record.status == 7):
            return super().get_data()

    def get_value(self, record):
        return {
            "status": str(record.status),
            "status_date": record.status_date,
            "status_summary": record.status_summary,
            "sub_status": record.sub_status,
            "sub_status_other":record.sub_status_other,
        }


class SummaryHistoryItem(BaseBarrierHistoryItem):
    field = "summary"


class TagsHistoryItem(BaseBarrierHistoryItem):
    field = "tags"

    def get_value(self, record):
        return record.tags_cache or []


class TitleHistoryItem(BaseBarrierHistoryItem):
    field = "barrier_title"


class BarrierHistoryFactory(HistoryItemFactory):
    """
    Polymorphic wrapper for barrier HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        ArchivedHistoryItem,
        CategoriesHistoryItem,
        CompaniesHistoryItem,
        IsSummarySensitiveHistoryItem,
        LocationHistoryItem,
        PriorityHistoryItem,
        ProductHistoryItem,
        ScopeHistoryItem,
        SectorsHistoryItem,
        SourceHistoryItem,
        StatusHistoryItem,
        SummaryHistoryItem,
        TagsHistoryItem,
        TitleHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id, start_date=None):
        """
        Only show history after the reported_on date

        Note that history_date is set slightly after reported_on when submitting,
        so this will still return one history item for when the barrier was submitted,
        - we need this to compare subsequent history items against.
        """
        history = BarrierInstance.history.filter(id=barrier_id)
        if start_date:
            history = history.filter(history_date__gt=start_date)
        return history.order_by("history_date")
