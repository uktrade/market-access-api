from api.barriers.models import Barrier
from api.history.factories.base import HistoryItemFactoryBase
from api.history.items.barriers import (
    ArchivedHistoryItem,
    PriorityHistoryItem,
    StatusHistoryItem,
    TopPriorityHistoryItem,
)


class BarrierHistoryFactory(HistoryItemFactoryBase):
    """
    Polymorphic wrapper for barrier HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        ArchivedHistoryItem,
        PriorityHistoryItem,
        StatusHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return Barrier.history.filter(id=barrier_id).order_by("history_date")


class BarrierHistoryRemnantsFactory(HistoryItemFactoryBase):
    """
    TODO: Remaining legacy history items that arent refactored yet
    """

    class_lookup = {}
    history_item_classes = (TopPriorityHistoryItem,)
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return Barrier.history.filter(id=barrier_id).order_by("history_date")
