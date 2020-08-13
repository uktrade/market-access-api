from .base import BaseHistoryItem


class BaseAssessmentHistoryItem(BaseHistoryItem):
    model = "assessment"


class CommercialValueHistoryItem(BaseAssessmentHistoryItem):
    field = "commercial_value"


class CommercialValueExplanationHistoryItem(BaseAssessmentHistoryItem):
    field = "commercial_value_explanation"


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
