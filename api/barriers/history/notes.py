from api.interactions.models import Interaction
from .base import BaseHistoryItem, HistoryItemFactoryBase


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


class NoteHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        DocumentsHistoryItem,
        NoteTextHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return Interaction.history.filter(
            barrier_id=barrier_id
        ).order_by("id", "history_date")
