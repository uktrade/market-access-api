from rest_framework import serializers

from api.action_plans.models import (
    ActionPlan,
    ActionPlanMilestone,
    ActionPlanTask,
    Stakeholder,
)


class ActionPlanStakeholderSerializer(serializers.ModelSerializer):
    from rest_framework.fields import empty

    def run_validation(self, data=empty):
        return super().run_validation(data)

    class Meta:
        model = Stakeholder
        fields = (
            "id",
            "action_plan",
            "name",
            "status",
            "organisation",
            "job_title",
            "is_organisation",
        )


class ActionPlanTaskSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.SerializerMethodField()
    action_type_display = serializers.SerializerMethodField()

    class Meta:
        model = ActionPlanTask
        fields = (
            "id",
            "milestone",
            "action_text",
            "status",
            "start_date",
            "completion_date",
            "reason_for_completion_date_change",
            "action_text",
            "action_type",
            "action_type_category",
            "assigned_stakeholders",
            "action_type_display",
            "assigned_to",
            "assigned_to_email",
            "outcome",
            "progress",
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

    tasks = serializers.SerializerMethodField()
    estimated_completion_date = serializers.SerializerMethodField()

    def get_estimated_completion_date(self, obj):
        # latest value of estimated_completion_date for all tasks in milestone
        relevant_task = (
            obj.tasks.exclude(status="COMPLETED")
            .filter(completion_date__isnull=False)
            .order_by("-completion_date")
            .first()
        )
        if relevant_task:
            # Use format e.g. May 2023
            return relevant_task.completion_date.strftime("%b %Y")
        return None

    def get_tasks(self, obj):
        # order tasks by completion_date, descending, and place tasks with status == COMPLETED at the end
        tasks = obj.tasks.all()
        tasks = tasks.order_by("completion_date")
        completed_tasks = tasks.filter(status="COMPLETED")
        in_progress_tasks = tasks.exclude(status="COMPLETED")
        tasks = [*in_progress_tasks, *completed_tasks]
        return ActionPlanTaskSerializer(tasks, many=True).data

    class Meta:
        model = ActionPlanMilestone
        fields = (
            "id",
            "action_plan",
            "objective",
            "completion_date",
            "tasks",
            "estimated_completion_date",
        )


class ActionPlanSerializer(serializers.ModelSerializer):

    milestones = ActionPlanMilestoneSerializer(many=True)
    owner_email = serializers.SerializerMethodField()
    owner_full_name = serializers.SerializerMethodField()
    stakeholders = ActionPlanStakeholderSerializer(many=True, read_only=True)

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
            "owner_full_name",
            "status",
            "strategic_context",
            "strategic_context_last_updated",
            # risks and mitigations fields
            "has_risks",
            "potential_unwanted_outcomes",
            "potential_risks",
            "risk_level",
            "risk_mitigation_measures",
            # stakeholders fields
            "stakeholders",
        )
        lookup_field = "barrier"

    def get_owner_email(self, obj):
        if obj.owner:
            return obj.owner.email

    def get_owner_full_name(self, obj):
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
