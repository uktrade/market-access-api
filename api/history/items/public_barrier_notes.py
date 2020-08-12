from api.interactions.models import PublicBarrierNote
from .base import BaseHistoryItem
from ..factories.base import HistoryItemFactoryBase


class BaseNoteHistoryItem(BaseHistoryItem):
    model = "public_barrier_note"

    def get_barrier_id(self):
        return self.new_record.instance.barrier.id


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
