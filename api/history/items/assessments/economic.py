from ..base import BaseHistoryItem


class BaseAssessmentHistoryItem(BaseHistoryItem):
    model = "economic_assessment"


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


class ImportMarketSizeHistoryItem(BaseAssessmentHistoryItem):
    field = "import_market_size"


class RatingHistoryItem(BaseAssessmentHistoryItem):
    field = "rating"


class ValueToEconomyHistoryItem(BaseAssessmentHistoryItem):
    field = "value_to_economy"
