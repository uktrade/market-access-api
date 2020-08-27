from api.metadata.utils import (
    get_country,
    get_trading_bloc,
)
from .base import BaseHistoryItem


class BasePublicBarrierHistoryItem(BaseHistoryItem):
    model = "public_barrier"


class CategoriesHistoryItem(BasePublicBarrierHistoryItem):
    field = "categories"

    def get_value(self, record):
        return record.categories_cache or []


class LocationHistoryItem(BasePublicBarrierHistoryItem):
    field = "location"

    def get_value(self, record):
        value = {
            "country": None,
            "trading_bloc": None,
        }
        if record.trading_bloc:
            value["trading_bloc"] = get_trading_bloc(record.trading_bloc)
        if record.country:
            value["country"] = get_country(str(record.country))
        return value


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
