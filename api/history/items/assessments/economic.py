from ..base import BaseHistoryItem


class BaseEconomicAssessmentHistoryItem(BaseHistoryItem):
    model = "economic_assessment"


class ApprovedHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "approved"


class ArchivedHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "archived"


class DocumentsHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "documents"

    def get_value(self, record):
        return record.documents_cache or []


class ExplanationHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "explanation"

    def is_valid(self):
        return self.get_old_value().strip() != self.get_new_value().strip()


class ExportValueHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "export_value"


class ImportMarketSizeHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "import_market_size"


class RatingHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "rating"

    def get_value(self, record):
        if record.rating:
            return {
                "id": record.rating,
                "name": record.get_rating_display(),
            }


class ReadyForApprovalHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "ready_for_approval"


class ValueToEconomyHistoryItem(BaseEconomicAssessmentHistoryItem):
    field = "value_to_economy"
