from api.interactions.models import Interaction
from .base import BaseHistoryItem, HistoryItemFactory


class BaseNoteHistoryItem(BaseHistoryItem):
    model = "note"

    def get_new_value(self):
        if self.new_record.archived:
            return self.empty_value
        return super().get_new_value()

    def get_old_value(self):
        if self.new_record.archived:
            return super().get_old_value()
        return self.empty_value


class NoteTextHistoryItem(BaseNoteHistoryItem):
    field = "text"
    empty_value = ""


class DocumentsHistoryItem(BaseNoteHistoryItem):
    field = "documents"
    empty_value = []

    def get_value(self, record):
        return record.documents_cache or []


class NoteHistoryFactory(HistoryItemFactory):
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
