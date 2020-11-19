from api.assessment.models import EconomicAssessment
from ..base import HistoryItemFactoryBase
from ...items.assessments.economic import (
    ApprovedHistoryItem,
    ArchivedHistoryItem,
    DocumentsHistoryItem,
    ExplanationHistoryItem,
    ExportValueHistoryItem,
    ImportMarketSizeHistoryItem,
    RatingHistoryItem,
    ReadyForApprovalHistoryItem,
    ValueToEconomyHistoryItem,
)


class EconomicAssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ApprovedHistoryItem,
        ArchivedHistoryItem,
        DocumentsHistoryItem,
        ExplanationHistoryItem,
        ExportValueHistoryItem,
        ImportMarketSizeHistoryItem,
        RatingHistoryItem,
        ReadyForApprovalHistoryItem,
        ValueToEconomyHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return EconomicAssessment.history.filter(barrier_id=barrier_id).order_by("id", "history_date")
