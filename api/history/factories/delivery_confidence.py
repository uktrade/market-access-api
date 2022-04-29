import logging

from api.barriers.models import BarrierProgressUpdate

from ..items.delivery_confidence import (  # NextStepsHistoryItem,; ProgressUpdateNoteHistoryItem,
    DeliveryConfidenceHistoryItem,
)
from .base import HistoryItemFactoryBase

logger = logging.getLogger(__name__)


class DeliveryConfidenceHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        DeliveryConfidenceHistoryItem,
        # ProgressUpdateNoteHistoryItem,
        # NextStepsHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return BarrierProgressUpdate.history.filter(barrier_id=barrier_id).order_by(
            "history_date"
        )

    @classmethod
    def is_valid_change(cls, new_record, old_record):

        # Override method from HistoryItemFactoryBase, as we want
        # to display changes made to previous progress updates.

        if new_record.history_type not in cls.history_types:
            return False

        if new_record.history_type == "~" and old_record is None:
            return False

        if new_record.history_type == "-":
            return False
        return True

    @classmethod
    def get_old_record_for_progress_update(cls, new_record, full_history):
        if new_record.history_type == "+":
            # Check if the barrier has any previously created progress updates
            barrier_history_items = full_history.filter(
                barrier_id=new_record.barrier_id, history_type="+"
            )
            if new_record == barrier_history_items.first():
                # If the new record is the earliest history item in the list,
                # it does not need to be compared to anything
                return None
            else:
                # Get the history ID for the last created progress update
                last_created_progress_update_history = full_history.filter(
                    history_type="+", history_date__lt=new_record.history_date
                ).last()
                # Get the latest history item from the last created progress update
                last_update_for_last_created_history = full_history.filter(
                    id=last_created_progress_update_history.id,
                    history_date__lt=new_record.history_date,
                ).last()
                # Return that history item to compare it to the new record
                return last_update_for_last_created_history

        elif new_record.history_type == "~":
            # An update to an existing progress update should look at the last history
            # object of the matching progress_update
            # Ensure result is before the new_record was created,
            # or you'll accidently suck up any edits made in the future.
            progress_update_id = new_record.id
            progress_update_history_items = full_history.filter(
                id=progress_update_id,
                barrier_id=new_record.barrier_id,
                history_date__lt=new_record.history_date,
            ).last()
            return progress_update_history_items

    @classmethod
    def get_history_items(cls, barrier_id, fields=(), start_date=None):
        """Gets HistoryItems for all changes made to the object"""
        history_items = []

        history = cls.get_history(barrier_id)
        old_record = None

        for new_record in history:

            old_record = cls.get_old_record_for_progress_update(new_record, history)

            if start_date is None or new_record.history_date > start_date:
                history_items += cls.create_history_items(
                    new_record, old_record, fields
                )

        return history_items
