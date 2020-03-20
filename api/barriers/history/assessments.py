from .base import BaseHistoryItem, HistoryItemFactory


class ValueToEconomyHistoryItem(BaseHistoryItem):
    field = "value_to_economy"


class ImportMarketSizeHistoryItem(BaseHistoryItem):
    field = "import_market_size"


class CommercialValueHistoryItem(BaseHistoryItem):
    field = "commercial_value"


class ExportValueHistoryItem(BaseHistoryItem):
    field = "export_value"


class ExplanationHistoryItem(BaseHistoryItem):
    field = "explanation"


class ImpactHistoryItem(BaseHistoryItem):
    field = "impact"


class DocumentsHistoryItem(BaseHistoryItem):
    field = "documents"

    def get_value(self, record):
        return record.documents_cache


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
