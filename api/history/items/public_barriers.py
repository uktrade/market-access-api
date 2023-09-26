import datetime

from api.metadata.constants import BarrierStatus, PublicBarrierStatus
from api.metadata.utils import get_location_text

from .base import BaseHistoryItem
from ...barriers.models import Barrier


class BasePublicBarrierHistoryItem(BaseHistoryItem):
    model = "public_barrier"


class CategoriesHistoryItem(BasePublicBarrierHistoryItem):
    field = "categories"

    def get_value(self, record):
        return record.categories_cache or []


class LightTouchReviewsHistoryItem(BasePublicBarrierHistoryItem):
    field = "light_touch_reviews"

    def get_value(self, record):
        return record.light_touch_reviews_cache


class LocationHistoryItem(BasePublicBarrierHistoryItem):
    field = "location"

    def get_value(self, record):
        return get_location_text(
            country_id=record.country,
            trading_bloc=record.trading_bloc,
            caused_by_trading_bloc=record.caused_by_trading_bloc,
        )


class PublicViewStatusHistoryItem(BasePublicBarrierHistoryItem):
    field = "public_view_status"

    def get_value(self, record):
        try:
            barrier_record = record.barrier.history.as_of(
                record.history_date + datetime.timedelta(seconds=1)
            )
        except Barrier.DoesNotExist:
            # the barrier did not exist at that point.
            return {
                "public_view_status": {
                    "id": "",
                    "name": "",
                },
                "public_eligibility": "",
                "public_eligibility_summary": "",
            }

        return {
            "public_view_status": {
                "id": record.public_view_status,
                "name": PublicBarrierStatus.choices[record.public_view_status],
            },
            "public_eligibility": barrier_record.public_eligibility,
            "public_eligibility_summary": barrier_record.public_eligibility_summary,
        }


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

    def is_valid(self):
        return self.is_resolved(self.old_record) != self.is_resolved(self.new_record)

    def get_value(self, record):
        return {
            "status": str(record.status),
            "status_date": record.status_date,
            "is_resolved": self.is_resolved(record),
        }

    def is_resolved(self, record):
        if record:
            return record.status == BarrierStatus.RESOLVED_IN_FULL


class SummaryHistoryItem(BasePublicBarrierHistoryItem):
    field = "summary"


class TitleHistoryItem(BasePublicBarrierHistoryItem):
    field = "title"
