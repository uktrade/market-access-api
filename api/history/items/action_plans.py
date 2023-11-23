from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from api.history.items.base import BaseHistoryItem

AuthUser = get_user_model()


def get_default_user():
    # Getting my User object prepared
    try:
        obj = AuthUser.objects.filter(email="ciaran.doherty@digital.trade.gov.uk")
        if obj.exists():
            backup_user = obj.first()
        else:
            backup_user, _ = AuthUser.objects.get_or_create(
                email="ciaran.doherty@digital.trade.gov.uk",
                username="ciaran.doherty@digital.trade.gov.uk",
            )
    except Exception as exc:
        # If I do not exist we are using a test system
        # make a fake user with my email
        backup_user, _ = AuthUser.objects.get_or_create(
            email="ciaran.doherty@digital.trade.gov.uk",
            username="ciaran.doherty@digital.trade.gov.uk",
        )

    return backup_user


class ActionPlanHistoryItem(BaseHistoryItem):
    model = "action_plan"

    def get_barrier_id(self):
        return self.new_record.instance.barrier.id


class ActionPlanOwnerHistoryItem(ActionPlanHistoryItem):
    field = "owner"

    def get_empty_value(self):
        return None

    def get_value(self, record):
        try:
            # Check that the user exists
            user = getattr(record, "owner", None)
        except ObjectDoesNotExist:
            # default to me if user does not exist.
            backup_user = get_default_user()
            record.user = backup_user
            record.save()

        return self._format_user(record.owner).get("name")


class ActionPlanCurrentStatusHistoryItem(ActionPlanHistoryItem):
    field = "current_status"


class ActionPlanCurrentStatusLastUpdatedHistoryItem(ActionPlanHistoryItem):
    field = "current_status_last_updated"


class ActionPlanStatusHistoryItem(ActionPlanHistoryItem):
    field = "status"


class ActionPlanStrategicContextHistoryItem(ActionPlanHistoryItem):
    field = "strategic_context"


class ActionPlanMilestoneHistoryItem(BaseHistoryItem):
    model = "action_plan_milestone"

    def get_barrier_id(self):
        return self.new_record.instance.action_plan.barrier.id


class ActionPlanMilestoneObjectiveHistoryItem(ActionPlanMilestoneHistoryItem):
    field = "objective"


class ActionPlanMilestoneCompletionDateHistoryItem(ActionPlanMilestoneHistoryItem):
    field = "completion_date"


class ActionPlanTaskHistoryItem(BaseHistoryItem):
    model = "action_plan_task"

    def get_barrier_id(self):
        return self.new_record.instance.milestone.action_plan.barrier.id


class ActionPlanTaskStatusHistoryItem(ActionPlanTaskHistoryItem):
    field = "status"


class ActionPlanTaskStartDateHistoryItem(ActionPlanTaskHistoryItem):
    field = "start_date"


class ActionPlanTaskCompletionDateHistoryItem(ActionPlanTaskHistoryItem):
    field = "completion_date"

    def get_value(self, record):
        return record.completion_date


class ActionPlanTaskActionTextHistoryItem(ActionPlanTaskHistoryItem):
    field = "action_text"


class ActionPlanTaskActionTypeHistoryItem(ActionPlanTaskHistoryItem):
    field = "action_type"


class ActionPlanTaskActionTypeCategoryHistoryItem(ActionPlanTaskHistoryItem):
    field = "action_type_category"


class ActionPlanTaskAssignedToHistoryItem(ActionPlanTaskHistoryItem):
    field = "assigned_to"

    def get_empty_value(self):
        return None

    def get_value(self, record):
        try:
            # Check that the user exists
            user = getattr(record, "assigned_to", None)
        except ObjectDoesNotExist:
            # default to me if user does not exist.
            backup_user = get_default_user()
            record.user = backup_user
            record.save()

        return self._format_user(record.assigned_to).get("name")


class ActionPlanTaskStakeholdersHistoryItem(ActionPlanTaskHistoryItem):
    field = "stakeholders"


class ActionPlanTaskOutcomeHistoryItem(ActionPlanTaskHistoryItem):
    field = "outcome"


class ActionPlanTaskProgressHistoryItem(ActionPlanTaskHistoryItem):
    field = "progress"
