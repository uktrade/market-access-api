from api.assessment.models import EconomicAssessment
from ..base import HistoryItemFactoryBase
from ...items.assessments.economic_impact import (
    ExplanationHistoryItem,
    ImpactHistoryItem,
)


class EconomicImpactAssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ExplanationHistoryItem,
        ImpactHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return EconomicAssessment.history.filter(barrier_id=barrier_id).order_by("history_date")
