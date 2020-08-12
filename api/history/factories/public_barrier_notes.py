from api.interactions.models import PublicBarrierNote
from .base import HistoryItemFactoryBase
from ..items.public_barrier_notes import (
    ArchivedHistoryItem,
    TextHistoryItem,
)


class PublicBarrierNoteHistoryFactory(HistoryItemFactoryBase):
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
