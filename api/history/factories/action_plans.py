from api.action_plans.models import ActionPlan, ActionPlanMilestone, ActionPlanTask
from api.history.items.action_plans import (
    ActionPlanCurrentStatusHistoryItem,
    ActionPlanCurrentStatusLastUpdatedHistoryItem,
    ActionPlanMilestoneCompletionDateHistoryItem,
    ActionPlanMilestoneObjectiveHistoryItem,
    ActionPlanOwnerHistoryItem,
    ActionPlanStatusHistoryItem,
    ActionPlanStrategicContextHistoryItem,
    ActionPlanTaskActionTextHistoryItem,
    ActionPlanTaskActionTypeCategoryHistoryItem,
    ActionPlanTaskActionTypeHistoryItem,
    ActionPlanTaskAssignedToHistoryItem,
    ActionPlanTaskCompletionDateHistoryItem,
    ActionPlanTaskOutcomeHistoryItem,
    ActionPlanTaskProgressHistoryItem,
    ActionPlanTaskStakeholdersHistoryItem,
)

from .base import HistoryItemFactoryBase


class ActionPlanHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ActionPlanOwnerHistoryItem,
        ActionPlanCurrentStatusHistoryItem,
        ActionPlanStatusHistoryItem,
        ActionPlanCurrentStatusLastUpdatedHistoryItem,
        ActionPlanStrategicContextHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return ActionPlan.history.filter(barrier_id=barrier_id).order_by(
            "id", "history_date"
        )


class ActionPlanMilestoneHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ActionPlanMilestoneObjectiveHistoryItem,
        ActionPlanMilestoneCompletionDateHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return ActionPlanMilestone.history.filter(
            action_plan__barrier_id=barrier_id
        ).order_by("id", "history_date")


class ActionPlanTaskHistoryFactory(HistoryItemFactoryBase):
    class_lookup = {}
    history_item_classes = (
        ActionPlanTaskActionTextHistoryItem,
        ActionPlanTaskActionTypeHistoryItem,
        ActionPlanTaskActionTypeCategoryHistoryItem,
        ActionPlanTaskAssignedToHistoryItem,
        ActionPlanTaskStakeholdersHistoryItem,
        ActionPlanTaskOutcomeHistoryItem,
        ActionPlanTaskProgressHistoryItem,
        ActionPlanTaskCompletionDateHistoryItem,
    )
    history_types = ("+", "~")

    @classmethod
    def get_history(cls, barrier_id):
        return ActionPlanTask.history.filter(
            milestone__action_plan__barrier_id=barrier_id
        ).order_by("id", "history_date")
