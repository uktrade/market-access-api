from api.assessment.models import StrategicAssessment

from ...items.assessments.strategic import (
    AdditionalInformationHistoryItem,
    ApprovedHistoryItem,
    ArchivedHistoryItem,
    CompetitionHistoryItem,
    GovernmentPolicyHistoryItem,
    HMGStrategyHistoryItem,
    ScaleHistoryItem,
    TradingRelationsHistoryItem,
    UKGrantsHistoryItem,
    UKInterestAndSecurityHistoryItem,
)
from ..base import HistoryItemFactoryBase


class StrategicAssessmentHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ApprovedHistoryItem,
        ArchivedHistoryItem,
        HMGStrategyHistoryItem,
        GovernmentPolicyHistoryItem,
        TradingRelationsHistoryItem,
        UKInterestAndSecurityHistoryItem,
        UKGrantsHistoryItem,
        CompetitionHistoryItem,
        AdditionalInformationHistoryItem,
        ScaleHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return StrategicAssessment.history.filter(barrier_id=barrier_id).order_by(
            "id", "history_date"
        )
