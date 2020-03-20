from .base import BaseHistoryItem, HistoryItemFactory


class NoteTextHistoryItem(BaseHistoryItem):
    field = "text"


class DocumentsHistoryItem(BaseHistoryItem):
    field = "documents"

    def get_value(self, record):
        return record.documents_cache


class NotesHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        DocumentsHistoryItem,
        NoteTextHistoryItem,
    )
