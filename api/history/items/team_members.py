from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .base import BaseHistoryItem

backup_user = get_user_model().objects.get(email="ciaran.doherty@digital.trade.gov.uk")


class TeamMemberHistoryItem(BaseHistoryItem):
    model = "team_member"
    field = "user"

    def get_empty_value(self):
        return None

    def get_value(self, record):
        if record and not record.archived:
            try:
                user = getattr(record, "user", None)
            except ObjectDoesNotExist:
                record.user = backup_user
                record.save()

            return {
                "user": self._format_user(record.user),
                "role": record.role,
            }
