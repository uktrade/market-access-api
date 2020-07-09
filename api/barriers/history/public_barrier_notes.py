from api.interactions.models import PublicBarrierNote
from .base import BaseHistoryItem, HistoryItemFactory


class BaseNoteHistoryItem(BaseHistoryItem):
    model = "public_barrier_note"


class ArchivedHistoryItem(BaseNoteHistoryItem):
    field = "archived"

    def get_value(self, record):
        return {
            "archived": record.archived,
            "text": record.text,
        }


class TextHistoryItem(BaseNoteHistoryItem):
    field = "text"

    def get_value(self, record):
        return record.text


class PublicBarrierNoteHistoryFactory(HistoryItemFactory):
    class_lookup = {}
    history_item_classes = (
        ArchivedHistoryItem,
        TextHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return PublicBarrierNote.history.filter(
            public_barrier__barrier_id=barrier_id
        ).order_by("id", "history_date")
