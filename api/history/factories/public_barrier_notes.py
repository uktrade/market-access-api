from api.interactions.models import PublicBarrierNote

from ..items.public_barrier_notes import ArchivedHistoryItem, TextHistoryItem
from .base import HistoryItemFactoryBase


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
