from api.barriers.models import BarrierTopPrioritySummary
from api.history.items.base import BaseHistoryItem


class BaseBarrierHistoryItem(BaseHistoryItem):
    model = "barrier"

    def get_barrier_id(self):
        return self.new_record.instance.id


class ArchivedHistoryItem(BaseBarrierHistoryItem):
    field = "archived"

    def get_value(self, record):
        if record.archived:
            return {
                "archived": True,
                "archived_reason": record.archived_reason,
                "archived_explanation": record.archived_explanation,
            }
        else:
            return {
                "archived": False,
                "unarchived_reason": record.unarchived_reason,
            }


class PriorityHistoryItem(BaseBarrierHistoryItem):
    field = "priority"

    def get_value(self, record):
        priority = record.priority
        if priority is not None:
            priority = str(priority)
        return {
            "priority": priority,
            "priority_summary": record.priority_summary,
        }


class StatusHistoryItem(BaseBarrierHistoryItem):
    field = "status"

    def get_value(self, record):
        return {
            "status": str(record.status),
            "status_date": record.status_date,
            "status_summary": record.status_summary,
            "sub_status": record.sub_status,
            "sub_status_other": record.sub_status_other,
        }


class TopPriorityHistoryItem(BaseBarrierHistoryItem):
    field = "top_priority_status"

    def _get_top_priority_summary_text(self, record):
        """We want to get the top_priority_summary_text from the point in time when the change to the
        top_priority_status was made.
        """
        try:
            return (
                record.instance.top_priority_summary.first()
                .history.as_of(self.new_record.history_date)
                .top_priority_summary_text
            )
        # sometimes the BarrierTopPrioritySummary does not exist, at which point we return an empty string
        except (BarrierTopPrioritySummary.DoesNotExist, AttributeError):
            return ""

    def get_value(self, record):
        status = record.get_top_priority_status_display()
        if (
            record.top_priority_status == "APPROVED"
            or record.top_priority_status == "APPROVAL_PENDING"
            or record.top_priority_status == "REMOVAL_PENDING"
            or record.top_priority_status == "RESOLVED"
        ):
            # It's an accepted Top Priority Request, or pending review
            top_priority_reason = self._get_top_priority_summary_text(record)
        else:
            # The top_priority_status is NONE
            if record.top_priority_rejection_summary:
                # It's a rejected Top Priority Request
                status = "Rejected"
                top_priority_reason = record.top_priority_rejection_summary
            else:
                # The barrier has had its top-priority status removed
                status = "Removed"
                top_priority_reason = self._get_top_priority_summary_text(record)

        return {"value": status, "reason": top_priority_reason}
