from api.barriers.models import PublicBarrier
from .base import BaseHistoryItem, HistoryItemFactoryBase


class BasePublicBarrierHistoryItem(BaseHistoryItem):
    model = "public_barrier"


class CategoriesHistoryItem(BasePublicBarrierHistoryItem):
    field = "categories"

    def get_value(self, record):
        return record.categories_cache or []


class CountryHistoryItem(BasePublicBarrierHistoryItem):
    field = "country"


class PublicViewStatusHistoryItem(BasePublicBarrierHistoryItem):
    field = "public_view_status"


class SectorsHistoryItem(BasePublicBarrierHistoryItem):
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


class StatusHistoryItem(BasePublicBarrierHistoryItem):
    field = "status"

    def get_value(self, record):
        return {"status": str(record.status)}


class SummaryHistoryItem(BasePublicBarrierHistoryItem):
    field = "summary"


class TitleHistoryItem(BasePublicBarrierHistoryItem):
    field = "title"


class PublicBarrierHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        CategoriesHistoryItem,
        CountryHistoryItem,
        PublicViewStatusHistoryItem,
        SectorsHistoryItem,
        StatusHistoryItem,
        SummaryHistoryItem,
        TitleHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return PublicBarrier.history.filter(barrier_id=barrier_id).order_by("history_date")
