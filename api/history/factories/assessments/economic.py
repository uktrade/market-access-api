from api.assessment.models import EconomicAssessment
from ..base import HistoryItemFactoryBase
from ...items.assessments.economic import (
    CommercialValueHistoryItem,
    CommercialValueExplanationHistoryItem,
    DocumentsHistoryItem,
    ExplanationHistoryItem,
    ExportValueHistoryItem,
    ImportMarketSizeHistoryItem,
    RatingHistoryItem,
    ValueToEconomyHistoryItem,
)


class EconomicAssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        CommercialValueHistoryItem,
        CommercialValueExplanationHistoryItem,
        DocumentsHistoryItem,
        ExplanationHistoryItem,
        ExportValueHistoryItem,
        ImportMarketSizeHistoryItem,
        RatingHistoryItem,
        ValueToEconomyHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return EconomicAssessment.history.filter(barrier_id=barrier_id).order_by("history_date")
