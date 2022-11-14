from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from rest_framework import serializers

from api.action_plans.models import ActionPlan, ActionPlanTask
from api.collaboration.models import TeamMember
from api.history.models import CachedHistoryItem
from api.metadata.constants import (
    GOVERNMENT_ORGANISATION_TYPES,
    PROGRESS_UPDATE_CHOICES,
    TOP_PRIORITY_BARRIER_STATUS,
    BarrierStatus,
)

from ..models import BarrierProgressUpdate
from .base import BarrierSerializerBase
from .mixins import AssessmentFieldsMixin


class DataworkspaceActionPlanSerializer(serializers.ModelSerializer):
    strategic_context = serializers.SerializerMethodField()
    strategic_context_updated_on = serializers.SerializerMethodField()
    progress_update = serializers.SerializerMethodField()
    progress_update_updated_on = serializers.SerializerMethodField()
    action_plan_owner = serializers.SerializerMethodField()
    number_of_objectives = serializers.SerializerMethodField()
    number_of_objectives_complete = serializers.SerializerMethodField()
    number_of_interventions = serializers.SerializerMethodField()
    number_of_interventions_complete = serializers.SerializerMethodField()
    all_intervention_types = serializers.SerializerMethodField()
    action_plan_percent_complete = serializers.SerializerMethodField()

    class Meta:
        model = ActionPlan
        fields = (
            "strategic_context",
            "strategic_context_updated_on",
            "progress_update",
            "progress_update_updated_on",
            "action_plan_owner",
            "number_of_objectives",
            "number_of_objectives_complete",
            "number_of_interventions",
            "number_of_interventions_complete",
            "all_intervention_types",
            "action_plan_percent_complete",
        )

    def get_strategic_context(self, obj):
        return obj.strategic_context

    def get_strategic_context_updated_on(self, obj):
        return (
            obj.strategic_context_last_updated
            and obj.strategic_context_last_updated.strftime(
                settings.DEFAULT_EXPORT_DATE_FORMAT
            )
        )

    def get_progress_update(self, obj):
        return obj.current_status

    def get_progress_update_updated_on(self, obj):
        return (
            obj.current_status_last_updated
            and obj.current_status_last_updated.strftime(
                settings.DEFAULT_EXPORT_DATE_FORMAT
            )
        )

    def get_action_plan_owner(self, obj):
        if not obj.owner:
            return None
        return obj.owner.email

    def get_number_of_objectives(self, obj):
        return obj.milestones.count()

    def get_number_of_objectives_complete(self, obj):
        return (
            obj.milestones.annotate(
                incomplete_tasks=Count("tasks", filter=~Q(tasks__status="COMPLETED")),
                tasks_count=Count("tasks"),
            )
            .filter(incomplete_tasks=0, tasks_count__gt=0)
            .count()
        )

    def get_number_of_interventions(self, obj):
        return ActionPlanTask.objects.filter(milestone__action_plan=obj).count()

    def get_number_of_interventions_complete(self, obj):
        return ActionPlanTask.objects.filter(
            milestone__action_plan=obj, status="COMPLETED"
        ).count()

    def get_all_intervention_types(self, obj):
        intervention_types = [
            f"{task.action_type_category} - {task.get_action_type_display()}"
            for task in ActionPlanTask.objects.filter(milestone__action_plan=obj)
        ]
        return ",".join(intervention_types)

    def get_action_plan_percent_complete(self, obj):
        total_interventions = self.get_number_of_interventions(obj)
        if total_interventions == 0:
            return "N/A"
        num_complete_intervention = self.get_number_of_interventions_complete(obj)
        completion_percentage = (num_complete_intervention / total_interventions) * 100
        return f"{completion_percentage}%"


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name")

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class ProgressUpdateSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    modified_by = UserSerializer()
    archived_by = UserSerializer()
    unarchived_by = UserSerializer()
    status = serializers.SerializerMethodField()

    class Meta:
        model = BarrierProgressUpdate
        fields = (
            "created_on",
            "created_by",
            "modified_on",
            "modified_by",
            "archived",
            "archived_by",
            "archived_on",
            "archived_reason",
            "unarchived_reason",
            "unarchived_on",
            "unarchived_by",
            "id",
            "status",
            "update",
            "next_steps",
        )

    def get_status(self, obj):
        if obj.status is not None:
            return PROGRESS_UPDATE_CHOICES[obj.status]
        return None


class DataWorkspaceSerializer(AssessmentFieldsMixin, BarrierSerializerBase):
    status_history = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    action_plan_added = serializers.SerializerMethodField()
    action_plan = DataworkspaceActionPlanSerializer()
    latest_progress_update = ProgressUpdateSerializer()
    government_organisations = serializers.SerializerMethodField()
    resolved_date = serializers.SerializerMethodField()
    is_regional_trade_plan = serializers.SerializerMethodField()
    is_resolved_top_priority = serializers.SerializerMethodField()

    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "all_sectors",
            "archived",
            "archived_by",
            "archived_explanation",
            "archived_on",
            "archived_reason",
            "categories",
            "caused_by_trading_bloc",
            "code",
            "commercial_value",
            "commercial_value_explanation",
            "commodities",
            "companies",
            "country",
            "created_by",
            "created_on",
            "economic_assessment_eligibility",
            "economic_assessment_eligibility_summary",
            "economic_assessment_explanation",
            "economic_assessment_rating",
            "economic_assessments",
            "estimated_resolution_date",
            "government_organisations",
            "id",
            "import_market_size",
            "is_summary_sensitive",
            "top_priority_status",
            "is_resolved_top_priority",
            "is_top_priority",
            "latest_progress_update",
            "location",
            "modified_by",
            "modified_on",
            "other_source",
            "priority",
            "priority_level",
            "priority_summary",
            "product",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
            "public_eligibility_postponed",
            "resolvability_assessments",
            "sectors",
            "sectors_affected",
            "source",
            "status",
            "status_date",
            "status_history",
            "status_summary",
            "strategic_assessments",
            "sub_status",
            "sub_status_other",
            "summary",
            "tags",
            "team_count",
            "term",
            "title",
            "top_priority_status",
            "trade_category",
            "trade_direction",
            "trading_bloc",
            "unarchived_by",
            "unarchived_on",
            "unarchived_reason",
            "valuation_assessment_explanation",
            "valuation_assessment_rating",
            "valuation_assessment_midpoint",
            "valuation_assessment_midpoint_value",
            "value_to_economy",
            "wto_profile",
            "government_organisations",
            "action_plan_added",
            "action_plan",
            "completion_percent",
            "resolved_date",
            "is_regional_trade_plan",
        )

    def get_status_history(self, obj):
        history_items = CachedHistoryItem.objects.filter(
            barrier=obj,
            model="barrier",
            field="status",
        )
        status_lookup = dict(BarrierStatus.choices)
        return [
            {
                "date": item.date.isoformat(),
                "status": {
                    "id": item.new_record.status,
                    "name": status_lookup.get(item.new_record.status, "Unknown"),
                },
            }
            for item in history_items
        ]

    def get_team_count(self, obj):
        return TeamMember.objects.filter(barrier=obj).count()

    def get_action_plan_added(self, obj):
        if not obj.action_plan:
            return False
        return (
            ActionPlan.objects.get_active_action_plans()
            .filter(id=obj.action_plan.id)
            .exists()
        )

    def get_government_organisations(self, obj):
        return [
            org.name
            for org in obj.organisations.all()
            if org.organisation_type in GOVERNMENT_ORGANISATION_TYPES
        ]

    def get_resolved_date(self, obj):
        if obj.status_date and (obj.status == 4 or obj.status == 3):
            return obj.status_date
        else:
            return None

    def get_is_regional_trade_plan(self, obj):
        return obj.is_regional_trade_plan

    def get_is_resolved_top_priority(self, obj):
        return obj.top_priority_status == TOP_PRIORITY_BARRIER_STATUS.RESOLVED
