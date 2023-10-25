from api.metadata.constants import PROGRESS_UPDATE_CHOICES

from .base import BaseHistoryItem


class BaseProgressUpdateHistoryItem(BaseHistoryItem):
    model = "progress_update"


class DeliveryConfidenceHistoryItem(BaseProgressUpdateHistoryItem):
    field = "status"

    def get_value(self, record):
        return (
            {
                "status": PROGRESS_UPDATE_CHOICES._display_map.get(record.status, ""),
                "summary": record.update or "",
            }
            if not record.archived
            else {}
        )


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
