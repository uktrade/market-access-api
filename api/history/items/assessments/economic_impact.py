from ..base import BaseHistoryItem


class BaseEconomicImpactAssessmentHistoryItem(BaseHistoryItem):
    model = "economic_impact_assessment"

    def get_barrier_id(self):
        return self.new_record.instance.economic_assessment.barrier_id


class ArchivedHistoryItem(BaseEconomicImpactAssessmentHistoryItem):
    field = "archived"


class ExplanationHistoryItem(BaseEconomicImpactAssessmentHistoryItem):
    field = "explanation"


class ImpactHistoryItem(BaseEconomicImpactAssessmentHistoryItem):
    field = "impact"

    def get_value(self, record):
        if record.impact:
            return {
                "code": record.impact,
                "name": record.get_impact_display(),
            }
