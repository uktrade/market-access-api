from api.interactions.models import Interaction
from .base import BaseHistoryItem, HistoryItemFactory


class BaseNoteHistoryItem(BaseHistoryItem):
    model = "note"


class NoteTextHistoryItem(BaseNoteHistoryItem):
    field = "text"


class DocumentsHistoryItem(BaseNoteHistoryItem):
    field = "documents"

    def get_value(self, record):
        return record.documents_cache or []


class NoteHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        DocumentsHistoryItem,
        NoteTextHistoryItem,
    )

    @classmethod
    def get_history(cls, barrier_id):
        return Interaction.history.filter(
            barrier_id=barrier_id
        ).order_by("id", "history_date")
