from api.barriers.models import BarrierTopPrioritySummary
from .base import HistoryItemFactoryBase
from ..items.barriers import TopPrioritySummaryHistoryItem


class BarrierTopPrioritySummaryHistoryFactory(HistoryItemFactoryBase):
    """
    Polymorphic wrapper for barrier TopPrioritySummaryHistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (TopPrioritySummaryHistoryItem,)
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return BarrierTopPrioritySummary.history.filter(barrier_id=barrier_id).order_by(
            "history_date"
        )
