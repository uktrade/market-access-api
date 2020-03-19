from .base import BaseHistoryItem, HistoryItemFactory


class ArchivedHistoryItem(BaseHistoryItem):
    field = "archived"

    def get_field_info(self):
        if self.new_record.archived is True:
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


class BarrierHistoryFactory(HistoryItemFactory):
    """
    Polymorphic wrapper for barrier HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        ArchivedHistoryItem,
        CategoriesHistoryItem,
        CompaniesHistoryItem,
        DescriptionHistoryItem,
        EUExitRelatedHistoryItem,
        LocationHistoryItem,
        PriorityHistoryItem,
        ProductHistoryItem,
        SectorsHistoryItem,
        SourceHistoryItem,
        StatusHistoryItem,
        TitleHistoryItem,
    )
