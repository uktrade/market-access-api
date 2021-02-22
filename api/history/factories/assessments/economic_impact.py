from api.assessment.models import EconomicImpactAssessment

from ...items.assessments.economic_impact import (
    ArchivedHistoryItem,
    ExplanationHistoryItem,
    ImpactHistoryItem,
)
from ..base import HistoryItemFactoryBase


class EconomicImpactAssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ArchivedHistoryItem,
        ExplanationHistoryItem,
        ImpactHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return EconomicImpactAssessment.history.filter(
            economic_assessment__barrier_id=barrier_id
        ).order_by("id", "history_date")
