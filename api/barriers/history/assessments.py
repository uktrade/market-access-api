from api.assessment.models import Assessment
from .base import BaseHistoryItem, HistoryItemFactory


class BaseAssessmentHistoryItem(BaseHistoryItem):
    model = "assessment"


class CommercialValueHistoryItem(BaseAssessmentHistoryItem):
    field = "commercial_value"


class DocumentsHistoryItem(BaseAssessmentHistoryItem):
    field = "documents"

    def get_value(self, record):
        return record.documents_cache or []


class ExplanationHistoryItem(BaseAssessmentHistoryItem):
    field = "explanation"


class ExportValueHistoryItem(BaseAssessmentHistoryItem):
    field = "export_value"


class ImpactHistoryItem(BaseAssessmentHistoryItem):
    field = "impact"


class ImportMarketSizeHistoryItem(BaseAssessmentHistoryItem):
    field = "import_market_size"


class ValueToEconomyHistoryItem(BaseAssessmentHistoryItem):
    field = "value_to_economy"


class AssessmentHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        CommercialValueHistoryItem,
        DocumentsHistoryItem,
        ExplanationHistoryItem,
        ExportValueHistoryItem,
        ImpactHistoryItem,
        ImportMarketSizeHistoryItem,
        ValueToEconomyHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id, start_date=None):
        history = Assessment.history.filter(barrier_id=barrier_id)
        if start_date:
            history = history.filter(history_date__gt=start_date)
        return history.order_by("history_date")
