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
        return None

    def _format_user(self, user):
        if user is not None:
            return {"id": user.id, "name": cleansed_username(user)}

        return None


class TitleHistoryItem(BaseHistoryItem):
    field = "barrier_title"

    def get_data(self):
        return {
            "date": self.new_record.history_date,
            "field": self.change.field,
            "old_value": str(self.change.old),
            "new_value": str(self.change.new),
            "user": self._format_user(
                self.new_record.history_user
            ),
            "field_info": {

            },
        }


class ArchivedHistoryItem(BaseHistoryItem):
    field = "archived"

    def get_data(self):
        data = {
            "date": new_record.history_date,
            "field": self.change.field,
            "old_value": self.change.old,
            "new_value": self.change.new,
            "user": self._format_user(
                self.new_record.history_user
            ),
        }
        if change.new is True:
            data["field_info"] = {
                "archived_reason": self.new_record.archived_reason,
                "archived_explanation": self.new_record.archived_explanation,
            }
        else:
            data["field_info"] = {
                "unarchived_reason": self.new_record.unarchived_reason,
            }
        return data


class StatusHistoryItem(BaseHistoryItem):
    field = "status"

    def get_data(self):
        if not (self.change.old == 0 or self.change.old is None):
            return {
                "date": self.new_record.history_date,
                "field": self.change.field,
                "old_value": str(self.change.old),
                "new_value": str(self.change.new),
                "user": self._format_user(
                    self.new_record.history_user
                ),
                "field_info": {
                    "status_date": self.new_record.status_date,
                    "status_summary": self.new_record.status_summary,
                    "sub_status": self.new_record.sub_status,
                    "sub_status_other": self.new_record.sub_status_other,
                },
            }


class PriorityHistoryItem(BaseHistoryItem):
    field = "priority"

    def get_data(self):
        return {
            "date": self.new_record.history_date,
            "field": self.change.field,
            "old_value": str(self.change.old),
            "new_value": str(self.change.new),
            "user": self._format_user(
                self.new_record.history_user
            ),
            "field_info": {
                "priority_date": self.new_record.priority_date,
                "priority_summary": self.new_record.priority_summary,
            },
        }


class HistoryItem:
    """
    Polymorphic wrapper for HistoryItem classes
    """
    history_item_classes = (
        TitleHistoryItem, StatusHistoryItem, PriorityHistoryItem
    )

    def __new__(cls, change, new_record):
        for history_item_class in cls.history_item_classes:
            if change.field == history_item_class.field:
                return history_item_class(change, new_record)
        return BaseHistoryItem(change, new_record)
