from api.action_plans.models import ActionPlan, ActionPlanMilestone, ActionPlanTask
from api.user.serializers import UserListSerializer
from rest_framework import serializers


class ActionPlanTaskSerializer(serializers.ModelSerializer):

    assigned_to_email = serializers.SerializerMethodField()
    action_type_display = serializers.SerializerMethodField()

    class Meta:
        model = ActionPlanTask
        fields = (
            "id",
            "milestone",
            "status",
            "start_date",
            "completion_date",
            "action_text",
            "action_type",
            "action_type_category",
            "stakeholders",
            "action_type_display",
            "assigned_to",
            "assigned_to_email",
        )

    def get_assigned_to_email(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.email

    def get_action_type_display(self, obj):
        action_type = obj.get_action_type_display()
        action_type_category = obj.action_type_category
        if not action_type_category:
            return action_type
        if (action_type == "Other") and (obj.action_type_category == "Other"):
            return "Other"
        return f"{action_type} - {action_type_category}"


class ActionPlanMilestoneSerializer(serializers.ModelSerializer):

    tasks = ActionPlanTaskSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = ActionPlanMilestone
        fields = ("id", "action_plan", "objective", "completion_date", "tasks")


class ActionPlanSerializer(serializers.ModelSerializer):

    milestones = ActionPlanMilestoneSerializer(many=True)
    owner_email = serializers.SerializerMethodField()

    class Meta:
        model = ActionPlan
        fields = (
            "id",
            "barrier",
            "owner",
            "milestones",
            "current_status",
            "current_status_last_updated",
            "owner_email",
            "status",
        )
        lookup_field = "barrier"

    def get_owner_email(self, obj):
        if obj.owner:
            return obj.owner.email

