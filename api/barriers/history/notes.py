from .base import BaseHistoryItem, HistoryItemFactory


class NoteTextHistoryItem(BaseHistoryItem):
    field = "text"


class NotesHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        NoteTextHistoryItem,
    )
