from api.history.items.base import BaseHistoryItem


class ActionPlanHistoryItem(BaseHistoryItem):
    model = "action_plan"

    def get_barrier_id(self):
        return self.new_record.instance.barrier.id


class ActionPlanOwnerHistoryItem(ActionPlanHistoryItem):
    field = "owner"


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


class ActionPlanTaskActionTextHistoryItem(ActionPlanTaskHistoryItem):
    field = "action_text"


class ActionPlanTaskActionTypeHistoryItem(ActionPlanTaskHistoryItem):
    field = "action_type"


class ActionPlanTaskActionTypeCategoryHistoryItem(ActionPlanTaskHistoryItem):
    field = "action_type_category"


class ActionPlanTaskAssignedToHistoryItem(ActionPlanTaskHistoryItem):
    field = "assigned_to"


class ActionPlanTaskStakeholdersHistoryItem(ActionPlanTaskHistoryItem):
    field = "stakeholders"


class ActionPlanTaskOutcomeHistoryItem(ActionPlanTaskHistoryItem):
    field = "outcome"


class ActionPlanTaskProgressHistoryItem(ActionPlanTaskHistoryItem):
    field = "progress"
