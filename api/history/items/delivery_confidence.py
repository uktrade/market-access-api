from .base import BaseHistoryItem


class BaseProgressUpdateHistoryItem(BaseHistoryItem):
    model = "progress_update"


class DeliveryConfidenceHistoryItem(BaseProgressUpdateHistoryItem):
    field = "status"

    def get_value(self, record):
        if record.archived:
            return ""
        return record.status or ""


class ProgressUpdateNoteHistoryItem(BaseProgressUpdateHistoryItem):
    field = "update"

    def get_value(self, record):
        if record.archived:
            return ""
        return record.update or ""


class NextStepsHistoryItem(BaseProgressUpdateHistoryItem):
    field = "next_steps"

    def get_value(self, record):
        if record.archived:
            return ""
        return record.next_steps or ""
