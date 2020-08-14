from api.assessment.models import Assessment
from .base import HistoryItemFactoryBase
from ..items.assessments import (
    CommercialValueHistoryItem,
    CommercialValueExplanationHistoryItem,
    DocumentsHistoryItem,
    ExplanationHistoryItem,
    ExportValueHistoryItem,
    ImpactHistoryItem,
    ImportMarketSizeHistoryItem,
    ValueToEconomyHistoryItem,
)


class AssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        CommercialValueHistoryItem,
        CommercialValueExplanationHistoryItem,
        DocumentsHistoryItem,
        ExplanationHistoryItem,
        ExportValueHistoryItem,
        ImpactHistoryItem,
        ImportMarketSizeHistoryItem,
        ValueToEconomyHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return Assessment.history.filter(barrier_id=barrier_id).order_by("history_date")
