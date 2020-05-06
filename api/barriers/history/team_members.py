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
    def create_history_items(cls, new_record, old_record, fields=()):
        if new_record.history_type == "+":
            return [TeamMemberHistoryItem(new_record, None)]
        if new_record.history_type == "~":
            if new_record.id == old_record.id:
                return [TeamMemberHistoryItem(new_record, old_record)]
            else:
                return [TeamMemberHistoryItem(new_record, None)]
        return []

    @classmethod
    def get_history(cls, barrier_id, start_date=None):
        history = TeamMember.history.filter(barrier_id=barrier_id)
        return history.order_by("id", "history_date")
