import datetime
import typing

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from rest_framework import serializers

from api.action_plans.models import ActionPlan, ActionPlanTask
from api.barriers.fields import ExportTypeReportField, LineBreakCharField
from api.barriers.models import (
    Barrier,
    BarrierProgressUpdate,
    BarrierTopPrioritySummary,
)
from api.barriers.serializers.base import BarrierSerializerBase
from api.collaboration.models import TeamMember
from api.metadata import utils as metadata_utils
from api.metadata.constants import (
    GOVERNMENT_ORGANISATION_TYPES,
    PRIORITY_LEVELS,
    PROGRESS_UPDATE_CHOICES,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_DIRECTION_CHOICES,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.metadata.utils import get_barrier_tag_from_title


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
        )

    def get_status(self, obj):
        if obj.status is not None:
            return PROGRESS_UPDATE_CHOICES[obj.status]
        return None


class DataWorkspaceSerializer(BarrierSerializerBase):
    status_history = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    action_plan_added = serializers.SerializerMethodField()
    action_plan = DataworkspaceActionPlanSerializer()
    latest_progress_update = ProgressUpdateSerializer()
    government_organisations = serializers.SerializerMethodField()
    resolved_date = serializers.SerializerMethodField()
    is_regional_trade_plan = serializers.SerializerMethodField()
    is_resolved_top_priority = serializers.SerializerMethodField()
    estimated_resolution_updated_date = serializers.SerializerMethodField()
    date_of_priority_level = serializers.SerializerMethodField()
    date_of_top_priority_scoping = serializers.SerializerMethodField()
    first_estimated_resolution_date = serializers.SerializerMethodField()
    previous_estimated_resolution_date = serializers.SerializerMethodField()
    overseas_region = serializers.SerializerMethodField()
    programme_fund_progress_update_author = serializers.SerializerMethodField()
    programme_fund_progress_update_date = serializers.SerializerMethodField()
    programme_fund_progress_update_expenditure = serializers.SerializerMethodField()
    programme_fund_progress_update_milestones = serializers.SerializerMethodField()
    progress_update_author = serializers.SerializerMethodField()
    progress_update_date = serializers.SerializerMethodField()
    progress_update_message = serializers.SerializerMethodField()
    progress_update_next_steps = serializers.SerializerMethodField()
    progress_update_status = serializers.SerializerMethodField()
    top_priority_summary = serializers.SerializerMethodField()
    top_priority_requested_date = serializers.SerializerMethodField()
    proposed_top_priority_change_user = serializers.SerializerMethodField()
    proposed_estimated_resolution_date = serializers.SerializerMethodField()
    proposed_estimated_resolution_date_user = serializers.SerializerMethodField()
    proposed_estimated_resolution_date_created = serializers.SerializerMethodField()
    main_sector = serializers.SerializerMethodField()
    export_types = ExportTypeReportField(required=False)
    trade_direction = serializers.SerializerMethodField()
    export_description = LineBreakCharField(required=False)
    tags = serializers.SerializerMethodField()
    priority_level = serializers.SerializerMethodField()
    reported_by = serializers.SerializerMethodField()
    barrier_owner = serializers.SerializerMethodField()
    first_published_on = serializers.SerializerMethodField()
    valuation_assessment_explanation = serializers.SerializerMethodField()
    valuation_assessment_midpoint = serializers.SerializerMethodField()
    valuation_assessment_midpoint_value = serializers.SerializerMethodField()
    valuation_assessment_rating = serializers.SerializerMethodField()
    date_valuation_first_added = serializers.SerializerMethodField()
    import_market_size = serializers.SerializerMethodField()
    value_to_economy = serializers.SerializerMethodField()
    economic_assessment_explanation = serializers.SerializerMethodField()
    economic_assessment_rating = serializers.SerializerMethodField()
    date_top_priority_rationale_added = serializers.SerializerMethodField()
    policy_teams = serializers.SerializerMethodField()
    approvers_summary = serializers.SerializerMethodField()
    public_barrier_set_to_awaiting_approval_on = serializers.SerializerMethodField()
    public_barrier_set_to_awaiting_publication_on = serializers.SerializerMethodField()
    erd_pending = serializers.SerializerMethodField()

    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "all_sectors",
            "archived",
            "archived_by",
            "archived_explanation",
            "archived_on",
            "archived_reason",
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
            "reported_by",
            "reported_on",
            "barrier_owner",
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
            "first_published_on",
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
            "date_valuation_first_added",
            "value_to_economy",
            "wto_profile",
            "action_plan_added",
            "action_plan",
            "completion_percent",
            "resolved_date",
            "is_regional_trade_plan",
            "estimated_resolution_updated_date",
            "date_of_priority_level",
            "date_of_top_priority_scoping",
            "first_estimated_resolution_date",
            "previous_estimated_resolution_date",
            "overseas_region",
            "programme_fund_progress_update_author",
            "programme_fund_progress_update_date",
            "programme_fund_progress_update_expenditure",
            "programme_fund_progress_update_milestones",
            "progress_update_author",
            "progress_update_date",
            "progress_update_message",
            "progress_update_next_steps",
            "progress_update_status",
            "top_priority_summary",
            "top_priority_requested_date",
            "proposed_top_priority_change_user",
            "next_steps_items",
            "proposed_estimated_resolution_date",
            "proposed_estimated_resolution_date_user",
            "proposed_estimated_resolution_date_created",
            "estimated_resolution_date_change_reason",
            "start_date",
            "export_types",
            "is_currently_active",
            "trade_direction",
            "main_sector",
            "export_description",
            "tags",
            "policy_teams",
            "date_top_priority_rationale_added",
            "approvers_summary",
            "public_barrier_set_to_awaiting_approval_on",
            "public_barrier_set_to_awaiting_publication_on",
            "erd_pending",
        )

    def to_representation(self, instance):
        data = super(DataWorkspaceSerializer, self).to_representation(instance)
        date_values = [
            data["date_of_top_priority_scoping"],
            data["date_of_priority_level"],
            data["top_priority_requested_date"],
        ]
        date_values = [d for d in date_values if d is not None]
        if not date_values:
            date_values.append(
                datetime.datetime.strptime(
                    data["reported_on"], "%Y-%m-%dT%H:%M:%S.%f%z"
                ).strftime("%Y-%m-%d")
            )
        date_values = [
            datetime.datetime.strptime(d, "%Y-%m-%d")
            for d in date_values
            if d is not None
        ]

        date = min(date_values)
        date = date.strftime("%Y-%m-%d") if date else None
        data["date_barrier_first_prioritised"] = date
        return data

    @staticmethod
    def get_tags(obj):
        return [tag.title for tag in obj.tags.all()]

    def get_erd_pending(self, obj):
        qs = obj.estimated_resolution_date_request.all()
        print(qs)
        for q in qs:
            print(q.barrier, q.status)
        if not qs:
            return "None"

        erd_request = qs.first()

        if not erd_request.estimated_resolution_date:
            return "Delete pending"

        return "Extend pending"


    def get_policy_teams(self, obj):
        return ",".join([p.title for p in obj.policy_teams.all()])

    def get_status_history(self, obj):
        history = Barrier.get_history(
            barrier_id=obj.id, fields=["status"], track_first_item=True
        )
        status_lookup = dict(BarrierStatus.choices)
        return [
            {
                "date": item["date"].isoformat(),
                "status": {
                    "id": item["new_value"],
                    "name": status_lookup.get(item["new_value"], "Unknown"),
                },
            }
            for item in history
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

    def get_estimated_resolution_updated_date(self, instance):
        try:
            history = (
                instance.__class__.history.filter(id=instance.id)
                .exclude(estimated_resolution_date=instance.estimated_resolution_date)
                .latest("history_date")
            )
        except ObjectDoesNotExist:
            # Error case if barriers are missing history
            return None

        if history.estimated_resolution_date:
            return history.history_date.strftime("%Y-%m-%d")
        else:
            return None

    def get_previous_estimated_resolution_date(self, instance):
        try:
            history = (
                instance.__class__.history.filter(id=instance.id)
                .exclude(estimated_resolution_date=instance.estimated_resolution_date)
                .latest("history_date")
            )
        except ObjectDoesNotExist:
            # Error case if barriers are missing history
            return None

        if history.estimated_resolution_date:
            return history.estimated_resolution_date.strftime("%Y-%m-%d")
        else:
            return None

    def get_date_of_priority_level(self, instance):
        if instance.priority_level == PRIORITY_LEVELS.NONE:
            return

        history = instance.history.order_by("-history_date").values(
            "history_date", "priority_level"
        )

        for i, history_item in enumerate(history):
            if i == len(history) - 1:
                return history_item["history_date"].strftime("%Y-%m-%d")
            if history[i + 1]["priority_level"] != instance.priority_level:
                return history_item["history_date"].strftime("%Y-%m-%d")

    def get_date_of_top_priority_scoping(self, instance):
        priority_tag = get_barrier_tag_from_title("Scoping (Top 100 priority barrier)")
        priority_tag_id = priority_tag["id"]

        if not instance.tags.filter(id=priority_tag_id).exists():
            return

        history = instance.history.order_by("-history_date").values(
            "history_date", "tags_cache"
        )

        for i, history_item in enumerate(history):
            if i == len(history) - 1:
                return history_item["history_date"].strftime("%Y-%m-%d")
            if priority_tag_id not in history[i + 1]["tags_cache"]:
                return history_item["history_date"].strftime("%Y-%m-%d")

    def get_first_estimated_resolution_date(self, instance):
        history = instance.history.filter(
            estimated_resolution_date__isnull=False
        ).order_by("history_date")

        first = history.values("estimated_resolution_date").first()

        if not first:
            return

        return first["estimated_resolution_date"].strftime("%Y-%m-%d")

    def get_date_top_priority_rationale_added(self, instance):
        try:
            top_priority_summary = instance.top_priority_summary.latest("modified_on")
        except BarrierTopPrioritySummary.DoesNotExist:
            return

        return top_priority_summary.modified_on.strftime("%Y-%m-%d")

    def get_overseas_region(self, instance) -> typing.List[str]:
        if instance.country:
            country = metadata_utils.get_country(str(instance.country))
            if country:
                overseas_region = country.get("overseas_region")
                if overseas_region:
                    return [overseas_region.get("name")]
        elif instance.trading_bloc:
            overseas_regions = metadata_utils.get_trading_bloc_overseas_regions(
                instance.trading_bloc
            )
            return [region["name"] for region in overseas_regions]

    def get_programme_fund_progress_update_author(self, instance):
        if instance.latest_programme_fund_progress_update:
            author = instance.latest_programme_fund_progress_update.created_by
            first_name = getattr(author, "first_name", None)
            last_name = getattr(author, "last_name", None)
            return f"{first_name} {last_name}" if first_name and last_name else None

    def get_programme_fund_progress_update_date(self, instance):
        if instance.latest_programme_fund_progress_update:
            return instance.latest_programme_fund_progress_update.created_on
        return None

    def get_programme_fund_progress_update_expenditure(self, instance):
        if instance.latest_programme_fund_progress_update:
            return instance.latest_programme_fund_progress_update.expenditure

    def get_programme_fund_progress_update_milestones(self, instance):
        if instance.latest_programme_fund_progress_update:
            return (
                instance.latest_programme_fund_progress_update.milestones_and_deliverables
            )
        return None

    def get_progress_update_author(self, instance):
        if (
            instance.latest_progress_update
            and instance.latest_progress_update.created_by
        ):
            first_name = getattr(
                instance.latest_progress_update.created_by, "first_name"
            )
            last_name = getattr(instance.latest_progress_update.created_by, "last_name")
            return f"{first_name} {last_name}" if first_name and last_name else None

    def get_progress_update_date(self, instance):
        if instance.latest_progress_update:
            return instance.latest_progress_update.created_on
        return None

    def get_progress_update_message(self, instance):
        if instance.latest_progress_update:
            return instance.latest_progress_update.update

    def get_progress_update_next_steps(self, instance):
        if instance.latest_progress_update:
            return instance.latest_progress_update.next_steps
        return None

    def get_progress_update_status(self, instance):
        if instance.latest_progress_update:
            return instance.latest_progress_update.get_status_display()
        return None

    def get_top_priority_summary(self, instance):
        priority_summary = BarrierTopPrioritySummary.objects.filter(barrier=instance)
        if priority_summary:
            latest_summary = priority_summary.latest("modified_on")
            return latest_summary.top_priority_summary_text

    def get_proposed_top_priority_change_user(self, instance):
        try:
            top_priority_summary = instance.top_priority_summary.latest("modified_on")
        except BarrierTopPrioritySummary.DoesNotExist:
            return

        user = top_priority_summary.created_by
        if user:
            return f"{user.first_name} {user.last_name or ''}"

    def get_top_priority_requested_date(self, instance):
        pending_states = [
            TOP_PRIORITY_BARRIER_STATUS.APPROVAL_PENDING,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
        ]
        if instance.top_priority_status in [
            *pending_states,
            TOP_PRIORITY_BARRIER_STATUS.APPROVED,
            TOP_PRIORITY_BARRIER_STATUS.RESOLVED,
        ]:
            history = instance.history.order_by("-history_date").values_list(
                "top_priority_status", "history_date"
            )
            for i, (top_priority_status, history_date) in enumerate(history):
                if i == len(history) - 1:
                    return history_date.strftime("%Y-%m-%d")
                if (
                    top_priority_status in pending_states
                    and history[i + 1][0] not in pending_states
                ):
                    return history_date.strftime("%Y-%m-%d")

    def get_proposed_estimated_resolution_date(self, instance):
        # only show the proposed date if it is different to the current date
        if not instance.proposed_estimated_resolution_date:
            return None

        # compare to estimated_resolution_date
        if (
            instance.proposed_estimated_resolution_date
            == instance.estimated_resolution_date
        ):
            return None

        return instance.proposed_estimated_resolution_date.strftime("%Y-%m-%d")

    def get_proposed_estimated_resolution_date_created(self, instance):
        # only show the proposed date if it is different to the current date
        if not instance.proposed_estimated_resolution_date_created:
            return None

        # compare to estimated_resolution_date
        if (
            instance.proposed_estimated_resolution_date_created
            == instance.estimated_resolution_date
        ):
            return None
        return instance.proposed_estimated_resolution_date_created.strftime("%Y-%m-%d")

    def get_proposed_estimated_resolution_date_user(self, instance):
        # only show the proposed date if it is different to the current date
        if not instance.proposed_estimated_resolution_date:
            return None
        first_name = getattr(
            instance.proposed_estimated_resolution_date_user, "first_name"
        )
        last_name = getattr(
            instance.proposed_estimated_resolution_date_user, "last_name"
        )
        return f"{first_name} {last_name}" if first_name and last_name else None

    def get_main_sector(self, instance) -> typing.Optional[str]:
        main_sector = metadata_utils.get_sector(instance.main_sector)
        if main_sector:
            return main_sector["name"]
        elif instance.all_sectors:
            # if there is no main sector, but there are all sectors, return "All sectors"
            return "All sectors"

        return None

    def get_trade_direction(self, instance) -> typing.Optional[str]:
        if instance.trade_direction:
            return {str(x): y for x, y in TRADE_DIRECTION_CHOICES}.get(
                str(instance.trade_direction)
            )
        else:
            return None

    def get_priority_level(self, instance) -> typing.Optional[str]:
        if instance.priority_level == "NONE" and instance.top_priority_status in (
            "APPROVED",
            "REMOVAL_PENDING",
        ):
            return "PB100"
        return instance.priority_level

    def get_reported_by(self, obj):
        reported_by = None
        if hasattr(obj, "created_by"):
            first_name = getattr(obj.created_by, "first_name", None)
            last_name = getattr(obj.created_by, "last_name", None)
            reported_by = (
                f"{first_name} {last_name}" if first_name and last_name else None
            )

        return reported_by

    def get_barrier_owner(self, obj):
        barrier_owner = None
        if hasattr(obj, "barrier_team"):
            owner = obj.barrier_team.filter(role="Owner").first()
            if owner:
                first_name = getattr(owner.user, "first_name", None)
                last_name = getattr(owner.user, "last_name", None)
                barrier_owner = (
                    f"{first_name} {last_name}" if first_name and last_name else None
                )

        return barrier_owner

    def get_first_published_on(self, obj):
        if hasattr(obj, "public_barrier"):
            return obj.public_barrier.first_published_on

    def get_economic_assessment_rating(self, obj):
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.get_rating_display()

    def get_economic_assessment_explanation(self, obj):
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.explanation

    def get_value_to_economy(self, obj):
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.export_potential.get("uk_exports_affected")

    def get_import_market_size(self, obj):
        """Size of import market for affected product(s)"""
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.export_potential.get("import_market_size")

    def get_valuation_assessment_rating(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.rating

    def get_valuation_assessment_midpoint(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.midpoint

    def get_valuation_assessment_midpoint_value(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.midpoint_value

    def get_valuation_assessment_explanation(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.explanation

    def get_date_valuation_first_added(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.modified_on

    def get_approvers_summary(self, obj):
        if hasattr(obj, "public_barrier"):
            return obj.public_barrier.approvers_summary

    def get_public_barrier_set_to_awaiting_approval_on(self, obj):
        public_barrier = getattr(obj, "public_barrier")
        if not public_barrier:
            return

        first_historical_record = public_barrier.history.filter(
            _public_view_status=PublicBarrierStatus.APPROVAL_PENDING
        ).first()
        if first_historical_record:
            return first_historical_record.history_date.strftime("%Y-%m-%d")

    def get_public_barrier_set_to_awaiting_publication_on(self, obj):
        public_barrier = getattr(obj, "public_barrier")
        if not public_barrier:
            return

        first_historical_record = public_barrier.history.filter(
            _public_view_status=PublicBarrierStatus.PUBLISHING_PENDING
        ).first()
        if first_historical_record:
            return first_historical_record.history_date.strftime("%Y-%m-%d")
