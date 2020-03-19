from api.barriers.exceptions import HistoryItemNotFound
from api.core.utils import cleansed_username, get_changed_fields


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

    def get_value(self, record):
        return record.categories_cache


class CompaniesHistoryItem(BaseHistoryItem):
    field = "companies"


class DescriptionHistoryItem(BaseHistoryItem):
    field = "problem_description"


class EUExitRelatedHistoryItem(BaseHistoryItem):
    field = "eu_exit_related"


class LocationHistoryItem(BaseHistoryItem):
    field = "location"

    def get_value(self, record):
        return {
            "country": record.export_country,
            "admin_areas": record.country_admin_areas,
        }


class PriorityHistoryItem(BaseHistoryItem):
    field = "priority"

    def get_value(self, record):
        if record.priority:
            return str(record.priority)

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
        if not (self.old_record.status == 0 or self.old_record.status is None):
            return super().get_data()

    def get_value(self, record):
        if record.status:
            return str(record.status)

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


class BarrierHistoryFactory(HistoryItemFactory):
    """
    Polymorphic wrapper for barrier HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        TitleHistoryItem, StatusHistoryItem, PriorityHistoryItem,
        ArchivedHistoryItem, EUExitRelatedHistoryItem, DescriptionHistoryItem,
        ProductHistoryItem, SourceHistoryItem, SectorsHistoryItem,
        CategoriesHistoryItem, CompaniesHistoryItem, LocationHistoryItem,
    )


class NotesHistoryFactory(HistoryItemFactory):
    """
    Polymorphic wrapper for note HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        NoteTextHistoryItem,
    )


class TeamMemberHistoryItem(BaseHistoryItem):
    field = "team_member"

    def get_value(self, record):
        if record and not record.archived:
            return {
                "user": self._format_user(record.user),
                "role": record.role,
            }


class TeamHistoryFactory:
    """
    Polymorphic wrapper for team HistoryItem classes
    """

    @classmethod
    def get_history_data(cls, new_record, old_record):
        if new_record.history_type == "+":
            return [TeamMemberHistoryItem(new_record, None).data]
        if new_record.history_type == "~":
            if new_record.user == old_record.user:
                return [TeamMemberHistoryItem(new_record, old_record).data]
        return []
