from api.interactions.models import Interaction
from .base import BaseHistoryItem, HistoryItemFactory


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


class NoteHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        DocumentsHistoryItem,
        NoteTextHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id, start_date=None):
        history = Interaction.history.filter(barrier_id=barrier_id)
        if start_date:
            history = history.filter(history_date__gt=start_date)
        return history.order_by("id", "history_date")
