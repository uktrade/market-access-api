from ..base import BaseHistoryItem


class BaseStrategicAssessmentHistoryItem(BaseHistoryItem):
    model = "strategic_assessment"


class ApprovedHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "approved"


class ArchivedHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "archived"


class HMGStrategyHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "hmg_strategy"


class GovernmentPolicyHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "government_policy"


class TradingRelationsHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "trading_relations"


class UKInterestAndSecurityHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "uk_interest_and_security"


class UKGrantsHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "uk_grants"


class CompetitionHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "competition"


class AdditionalInformationHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "additional_information"


class ScaleHistoryItem(BaseStrategicAssessmentHistoryItem):
    field = "scale"

    def get_value(self, record):
        if record.scale:
            return {
                "id": record.scale,
                "name": record.get_scale_display(),
            }
