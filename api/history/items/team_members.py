"""
From the fix for MAR-919 we have left 79 orphaned histories.
To fix this, the orphaned histories are a set to have the default user (me)
I can't help with any of histories but I can  stop the page crashing.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .base import BaseHistoryItem

# Getting my User object prepared
backup_user = get_user_model().objects.get(email="ciaran.doherty@digital.trade.gov.uk")


class TeamMemberHistoryItem(BaseHistoryItem):
    model = "team_member"
    field = "user"

    def get_empty_value(self):
        return None

    def get_value(self, record):
        if record and not record.archived:
            try:
                # Check that the user exists
                user = getattr(record, "user", None)
            except ObjectDoesNotExist:
                # default to me if user does not exist.
                record.user = backup_user
                record.save()

            return {
                "user": self._format_user(record.user),
                "role": record.role,
            }
