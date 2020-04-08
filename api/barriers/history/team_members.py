from api.collaboration.models import TeamMember
from .base import BaseHistoryItem, HistoryItemFactory


class TeamMemberHistoryItem(BaseHistoryItem):
    model = "team_member"
    field = "user"

    def get_value(self, record):
        if record and not record.archived:
            return {
                "user": self._format_user(record.user),
                "role": record.role,
            }


class TeamMemberHistoryFactory(HistoryItemFactory):

    @classmethod
    def create_history_items(cls, new_record, old_record, fields=[]):
        if new_record.history_type == "+":
            return [TeamMemberHistoryItem(new_record, old_record)]
        if new_record.history_type == "~":
            if new_record.user == old_record.user:
                return [TeamMemberHistoryItem(new_record, old_record)]
        return []

    @classmethod
    def get_history(cls, barrier_id, start_date=None):
        history = TeamMember.history.filter(barrier_id=barrier_id)
        if start_date:
            history = history.filter(history_date__gt=start_date)
        return history.order_by("user", "history_date")
