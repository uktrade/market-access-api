from api.interactions.models import Interaction

from ..items.notes import DocumentsHistoryItem, NoteTextHistoryItem
from .base import HistoryItemFactoryBase


class NoteHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        DocumentsHistoryItem,
        NoteTextHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return Interaction.history.filter(barrier_id=barrier_id).order_by(
            "id", "history_date"
        )
