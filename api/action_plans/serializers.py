from api.action_plans.models import ActionPlan, ActionPlanMilestone, ActionPlanTask
from api.user.serializers import UserListSerializer
from rest_framework import serializers


class ActionPlanTaskSerializer(serializers.ModelSerializer):

    # assigned_to = UserListSerializer(many=False)

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
        return obj.assigned_to.email

    def get_action_type_display(self, obj):
        return f"{obj.get_action_type_display()} - {obj.action_type_category}"


class ActionPlanMilestoneSerializer(serializers.ModelSerializer):

    tasks = ActionPlanTaskSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = ActionPlanMilestone
        fields = ("id", "action_plan", "objective", "completion_date", "tasks")


class ActionPlanSerializer(serializers.ModelSerializer):

    milestones = ActionPlanMilestoneSerializer(many=True)

    class Meta:
        model = ActionPlan
        fields = ("id", "barrier", "owner", "milestones")
        lookup_field = "barrier"

