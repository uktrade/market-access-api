from api.core.utils import cleansed_username
from api.history.exceptions import HistoryItemNotFound
from api.history.utils import get_changed_fields


class BaseHistoryItem:
    _data = None

    def __init__(self, new_record, old_record):
        self.new_record = new_record
        self.old_record = old_record

    def get_barrier_id(self):
        return self.new_record.instance.barrier_id

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
            "old_value": self.get_old_value(),
            "new_value": self.get_new_value(),
            "user": self._format_user(
                self.new_record.history_user
            ),
        }
        if hasattr(self, "get_field_info"):
            data['field_info'] = self.get_field_info()
        return data

    def get_new_value(self):
        if self.new_record:
            return self.get_value(self.new_record)

    def get_old_value(self):
        if self.old_record:
            return self.get_value(self.old_record)

    def get_value(self, record):
        return getattr(record, self.field)

    def is_valid(self):
        return True

    def _format_user(self, user):
        if user is not None:
            return {"id": user.id, "name": cleansed_username(user)}

        return None
