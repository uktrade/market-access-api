from .base import BaseHistoryItem, HistoryItemFactory


class TeamMemberHistoryItem(BaseHistoryItem):
    field = "team_member"

    def get_value(self, record):
        if record and not record.archived:
            return {
                "user": self._format_user(record.user),
                "role": record.role,
            }


class TeamMemberHistoryFactory:

    @classmethod
    def get_history_data(cls, new_record, old_record):
        if new_record.history_type == "+":
            return [TeamMemberHistoryItem(new_record, old_record).data]
        if new_record.history_type == "~":
            if new_record.user == old_record.user:
                return [TeamMemberHistoryItem(new_record, old_record).data]
        return []
