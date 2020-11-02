from ..base import BaseHistoryItem


class BaseResolvabilityAssessmentHistoryItem(BaseHistoryItem):
    model = "resolvability_assessment"


class ApprovedHistoryItem(BaseResolvabilityAssessmentHistoryItem):
    field = "approved"


class ArchivedHistoryItem(BaseResolvabilityAssessmentHistoryItem):
    field = "archived"


class EffortToResolveHistoryItem(BaseResolvabilityAssessmentHistoryItem):
    field = "effort_to_resolve"

    def get_value(self, record):
        return {
            "id": record.effort_to_resolve,
            "name": record.get_effort_to_resolve_display(),
        }


class ExplanationHistoryItem(BaseResolvabilityAssessmentHistoryItem):
    field = "explanation"


class TimeToResolveHistoryItem(BaseResolvabilityAssessmentHistoryItem):
    field = "time_to_resolve"

    def get_value(self, record):
        return {
            "id": record.time_to_resolve,
            "name": record.get_time_to_resolve_display(),
        }
