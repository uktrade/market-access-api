from api.interactions.models import Interaction
from .base import BaseHistoryItem
from ..factories.base import HistoryItemFactoryBase


class BaseNoteHistoryItem(BaseHistoryItem):
    model = "note"


class NoteTextHistoryItem(BaseNoteHistoryItem):
    field = "text"

    def get_value(self, record):
        if record.archived:
            return ""
        return record.text or ""


class DocumentsHistoryItem(BaseNoteHistoryItem):
    field = "documents"

    def get_value(self, record):
        if record.archived:
            return []
        return record.documents_cache or []
