from api.barriers.exceptions import HistoryItemNotFound
from api.core.utils import cleansed_username
from .utils import get_changed_fields


class BaseHistoryItem:
    _data = None

    def __init__(self, new_record, old_record):
        self.new_record = new_record
        self.old_record = old_record

    @property
    def data(self):
        if self._data is None:
            self._data = self.get_data()
        return self._data

    def get_data(self):
        data = {
            "date": self.new_record.history_date,
            "model": self.model,
            "field": self.field,
            "old_value": self.get_value(self.old_record),
            "new_value": self.get_value(self.new_record),
            "user": self._format_user(
                self.new_record.history_user
            ),
        }
        if hasattr(self, "get_field_info"):
            data['field_info'] = self.get_field_info()
        return data

    def get_value(self, record):
        return getattr(record, self.field)

    def _format_user(self, user):
        if user is not None:
            return {"id": user.id, "name": cleansed_username(user)}

        return None


class HistoryItemFactory:
    history_item_classes = tuple()
    class_lookup = {}

    @classmethod
    def create(cls, field, new_record, old_record):
        if not cls.class_lookup:
            cls.init_class_lookup()

        history_item_class = cls.class_lookup.get(field)
        if not history_item_class:
            raise HistoryItemNotFound
        return history_item_class(new_record, old_record)

    @classmethod
    def get_history_data(cls, new_record, old_record):
        if (
            old_record is not None
            and old_record.instance.pk == new_record.instance.pk
        ):
            if new_record.history_type != "+":
                changed_fields = get_changed_fields(new_record, old_record)

                for changed_field in changed_fields:
                    try:
                        history_item = cls.create(changed_field, new_record, old_record)
                        if history_item.data is not None:
                            yield history_item.data
                    except HistoryItemNotFound:
                        pass

    @classmethod
    def init_class_lookup(cls):
        for history_item_class in cls.history_item_classes:
            cls.class_lookup[history_item_class.field] = history_item_class
