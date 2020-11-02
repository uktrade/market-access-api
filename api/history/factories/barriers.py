from api.barriers.models import Barrier
from .base import HistoryItemFactoryBase
from ..items.barriers import (
    ArchivedHistoryItem,
    CategoriesHistoryItem,
    CausedByTradingBlocHistoryItem,
    CommoditiesHistoryItem,
    CompaniesHistoryItem,
    EndDateHistoryItem,
    IsSummarySensitiveHistoryItem,
    LocationHistoryItem,
    PriorityHistoryItem,
    ProductHistoryItem,
    PublicEligibilitySummaryHistoryItem,
    SectorsHistoryItem,
    SourceHistoryItem,
    StatusHistoryItem,
    SummaryHistoryItem,
    TagsHistoryItem,
    TermHistoryItem,
    TitleHistoryItem,
    TradeDirectionHistoryItem,
)


class BarrierHistoryFactory(HistoryItemFactoryBase):
    """
    Polymorphic wrapper for barrier HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        ArchivedHistoryItem,
        CategoriesHistoryItem,
        CausedByTradingBlocHistoryItem,
        CommoditiesHistoryItem,
        CompaniesHistoryItem,
        EndDateHistoryItem,
        IsSummarySensitiveHistoryItem,
        LocationHistoryItem,
        PriorityHistoryItem,
        ProductHistoryItem,
        PublicEligibilitySummaryHistoryItem,
        SectorsHistoryItem,
        SourceHistoryItem,
        StatusHistoryItem,
        SummaryHistoryItem,
        TagsHistoryItem,
        TermHistoryItem,
        TitleHistoryItem,
        TradeDirectionHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return Barrier.history.filter(id=barrier_id).order_by("history_date")
