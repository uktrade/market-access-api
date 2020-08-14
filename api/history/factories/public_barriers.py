from api.barriers.models import PublicBarrier
from .base import HistoryItemFactoryBase
from ..items.public_barriers import (
    CategoriesHistoryItem,
    CountryHistoryItem,
    PublicViewStatusHistoryItem,
    SectorsHistoryItem,
    StatusHistoryItem,
    SummaryHistoryItem,
    TitleHistoryItem,
)


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
