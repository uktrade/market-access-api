from ..exceptions import HistoryItemNotFound
from ..utils import get_changed_fields


class HistoryItemFactoryBase:
    """
    Base class for generating history items for a barrier
    """

    history_item_classes = tuple()
    class_lookup = {}
    history_types = ("+", "-", "~")

    @classmethod
    def create(cls, field, new_record, old_record):
        if not cls.class_lookup:
            cls.init_class_lookup()

        history_item_class = cls.class_lookup.get(field)
        if not history_item_class:
            raise HistoryItemNotFound
        return history_item_class(new_record, old_record)

    @classmethod
    def get_history(cls, barrier_id):
        """Fetch the history for a model"""
        raise NotImplementedError

    @classmethod
    def get_history_items(cls, barrier_id, fields=(), start_date=None):
        """Gets HistoryItems for all changes made to the object"""
        history_items = []
        history = cls.get_history(barrier_id)
        old_record = None

        for new_record in history:
            if start_date is None or new_record.history_date > start_date:
                history_items += cls.create_history_items(
                    new_record, old_record, fields
                )
            old_record = new_record

        return history_items

    @classmethod
    def create_history_items(cls, new_record, old_record, fields=()):
        """
        Create a HistoryItem to reflect each change made to the object

        If `fields` is supplied, only changes to those fields will be returned.
        """
        if not cls.is_valid_change(new_record, old_record):
            return

        changed_fields = get_changed_fields(new_record, old_record)

        for changed_field in changed_fields:
            if not fields or changed_field in fields:
                try:
                    history_item = cls.create(changed_field, new_record, old_record)
                    if history_item.is_valid():
                        yield history_item
                except HistoryItemNotFound:
                    pass

    @classmethod
    def is_valid_change(cls, new_record, old_record):
        if new_record.history_type not in cls.history_types:
            return False

        if old_record and old_record.instance.pk != new_record.instance.pk:
            return False

        if new_record.history_type == "~" and old_record is None:
            return False

        if new_record.history_type == "-":
            return False
        return True

    @classmethod
    def init_class_lookup(cls):
        """
        Initialise the class lookup so classes can be quickly fetched based on field
        """
        for history_item_class in cls.history_item_classes:
            cls.class_lookup[history_item_class.field] = history_item_class

    @classmethod
    def get_model(cls):
        for factory_class in cls.history_item_classes:
            return factory_class.model
