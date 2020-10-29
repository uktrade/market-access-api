from api.assessment.models import ResolvabilityAssessment
from ..base import HistoryItemFactoryBase
from ...items.assessments.resolvability import (
    ApprovedHistoryItem,
    ArchivedHistoryItem,
    EffortToResolveHistoryItem,
    ExplanationHistoryItem,
    TimeToResolveHistoryItem,
)


class ResolvabilityAssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ApprovedHistoryItem,
        ArchivedHistoryItem,
        EffortToResolveHistoryItem,
        ExplanationHistoryItem,
        TimeToResolveHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return ResolvabilityAssessment.history.filter(barrier_id=barrier_id).order_by("id", "history_date")
