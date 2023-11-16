from api.barriers.models import Barrier
from api.history.factories.base import HistoryItemFactoryBase
from api.history.items.barriers import (
    ArchivedHistoryItem,
    CategoriesHistoryItem,
    CausedByTradingBlocHistoryItem,
    CommercialValueExplanationHistoryItem,
    CommercialValueHistoryItem,
    CommoditiesHistoryItem,
    CompaniesHistoryItem,
    EconomicAssessmentEligibilityHistoryItem,
    EconomicAssessmentEligibilitySummaryHistoryItem,
    EndDateHistoryItem,
    IsSummarySensitiveHistoryItem,
    LocationHistoryItem,
    MainSectorHistoryItem,
    OrganisationsHistoryItem,
    ExportTypesHistoryItem,
    PriorityHistoryItem,
    PriorityLevelHistoryItem,
    ProductHistoryItem,
    PublicEligibilitySummaryHistoryItem,
    SectorsHistoryItem,
    SourceHistoryItem,
    StartDateHistoryItem,
    StatusHistoryItem,
    SummaryHistoryItem,
    TagsHistoryItem,
    TermHistoryItem,
    TitleHistoryItem,
    TopPriorityHistoryItem,
    TradeCategoryHistoryItem,
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
        CommercialValueHistoryItem,
        CommercialValueExplanationHistoryItem,
        CommoditiesHistoryItem,
        CompaniesHistoryItem,
        EconomicAssessmentEligibilityHistoryItem,
        EconomicAssessmentEligibilitySummaryHistoryItem,
        EndDateHistoryItem,
        StartDateHistoryItem,
        IsSummarySensitiveHistoryItem,
        LocationHistoryItem,
        MainSectorHistoryItem,
        PriorityLevelHistoryItem,
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
        TradeCategoryHistoryItem,
        TradeDirectionHistoryItem,
        OrganisationsHistoryItem,
        ExportTypesHistoryItem,
        TopPriorityHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id):
        return Barrier.history.filter(id=barrier_id).order_by("history_date")
