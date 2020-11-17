from ..base import BaseHistoryItem


class BaseEconomicImpactAssessmentHistoryItem(BaseHistoryItem):
    model = "economic_impact_assessment"


class ExplanationHistoryItem(BaseEconomicImpactAssessmentHistoryItem):
    field = "explanation"


class ImpactHistoryItem(BaseEconomicImpactAssessmentHistoryItem):
    field = "impact"
