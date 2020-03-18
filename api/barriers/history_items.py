from api.barriers.exceptions import HistoryItemNotFound
from api.core.utils import cleansed_username


class BaseHistoryItem:
    _data = None

    def __init__(self, change, new_record):
        self.change = change
        self.new_record = new_record

    @property
    def data(self):
        if self._data is None:
            self._data = self.get_data()
        return self._data

    def get_data(self):
        data = {
            "date": self.new_record.history_date,
            "field": self.change.field,
            "old_value": str(self.change.old),
            "new_value": str(self.change.new),
            "user": self._format_user(
                self.new_record.history_user
            ),
        }
        if hasattr(self, "get_field_info"):
            data['field_info'] = self.get_field_info()
        return data

    def _format_user(self, user):
        if user is not None:
            return {"id": user.id, "name": cleansed_username(user)}

        return None


class ArchivedHistoryItem(BaseHistoryItem):
    field = "archived"

    def get_field_info(self):
        if self.change.new is True:
            return {
                "archived_reason": self.new_record.archived_reason,
                "archived_explanation": self.new_record.archived_explanation,
            }
        else:
            return {
                "unarchived_reason": self.new_record.unarchived_reason,
            }


class CategoriesHistoryItem(BaseHistoryItem):
    field = "categories"


class DescriptionHistoryItem(BaseHistoryItem):
    field = "problem_description"


class EUExitRelatedHistoryItem(BaseHistoryItem):
    field = "eu_exit_related"


class PriorityHistoryItem(BaseHistoryItem):
    field = "priority"

    def get_field_info(self):
        return {
            "priority_date": self.new_record.priority_date,
            "priority_summary": self.new_record.priority_summary,
        }


class ProductHistoryItem(BaseHistoryItem):
    field = "product"


class SectorsHistoryItem(BaseHistoryItem):
    field = "sectors"


class SourceHistoryItem(BaseHistoryItem):
    field = "source"


class StatusHistoryItem(BaseHistoryItem):
    field = "status"

    def get_data(self):
        if not (self.change.old == 0 or self.change.old is None):
            return super().get_data()

    def get_field_info(self):
        return {
            "status_date": self.new_record.status_date,
            "status_summary": self.new_record.status_summary,
            "sub_status": self.new_record.sub_status,
            "sub_status_other": self.new_record.sub_status_other,
        }


class TitleHistoryItem(BaseHistoryItem):
    field = "barrier_title"


class NoteTextHistoryItem(BaseHistoryItem):
    field = "text"


class HistoryItemFactory:
    history_item_classes = tuple()
    class_lookup = {}

    @classmethod
    def create(cls, change, new_record):
        if not cls.class_lookup:
            cls.init_class_lookup()

        history_item_class = cls.class_lookup.get(change.field)
        if not history_item_class:
            raise HistoryItemNotFound
        return history_item_class(change, new_record)

    @classmethod
    def init_class_lookup(cls):
        for history_item_class in cls.history_item_classes:
            cls.class_lookup[history_item_class.field] = history_item_class


class BarrierHistoryItem(HistoryItemFactory):
    """
    Polymorphic wrapper for barrier HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        TitleHistoryItem, StatusHistoryItem, PriorityHistoryItem,
        ArchivedHistoryItem, EUExitRelatedHistoryItem, DescriptionHistoryItem,
        ProductHistoryItem, SourceHistoryItem, SectorsHistoryItem,
        CategoriesHistoryItem,
    )


class NotesHistoryItem(HistoryItemFactory):
    """
    Polymorphic wrapper for note HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        NoteTextHistoryItem,
    )
