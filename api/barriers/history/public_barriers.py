from api.barriers.models import PublicBarrier
from .base import BaseHistoryItem, HistoryItemFactory


class BaseBarrierHistoryItem(BaseHistoryItem):
    model = "public_barrier"


class CategoriesHistoryItem(BaseBarrierHistoryItem):
    field = "categories"

    def get_value(self, record):
        return record.categories_cache or []


class LocationHistoryItem(BaseBarrierHistoryItem):
    field = "location"

    def get_value(self, record):
        return {
            "country": str(record.export_country),
            "admin_areas": [
                str(admin_area) for admin_area in record.country_admin_areas or []
            ],
        }


class SectorsHistoryItem(BaseBarrierHistoryItem):
    field = "sectors"

    def get_data(self):
        if self.old_record or self.new_record:
            return super().get_data()

    def get_value(self, record):
        return [str(sector_id) for sector_id in record.sectors or []]


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


class TitleHistoryItem(BaseBarrierHistoryItem):
    field = "title"


class PublicBarrierHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        #CategoriesHistoryItem,
        LocationHistoryItem,
        SectorsHistoryItem,
        StatusHistoryItem,
        SummaryHistoryItem,
        TitleHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return PublicBarrier.history.filter(barrier_id=barrier_id).order_by("history_date")
