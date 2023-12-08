import datetime

from api.action_plans.models import ActionPlan, ActionPlanMilestone, ActionPlanTask
from api.barriers.models import (
    Barrier,
    BarrierTopPrioritySummary,
    ProgrammeFundProgressUpdate,
)
from api.history.factories import (
    BarrierHistoryFactory,
    DeliveryConfidenceHistoryFactory,
    EconomicAssessmentHistoryFactory,
    EconomicImpactAssessmentHistoryFactory,
    NoteHistoryFactory,
    PublicBarrierHistoryFactory,
    PublicBarrierNoteHistoryFactory,
    ResolvabilityAssessmentHistoryFactory,
    StrategicAssessmentHistoryFactory,
    TeamMemberHistoryFactory,
    WTOHistoryFactory,
)
from api.history.models import CachedHistoryItem
from api.history.v2.service import (
    convert_v2_history_to_legacy_object,
    enrich_full_history,
)


class HistoryManager:
    """
    Used for querying history items.

    Can either query the cache or generate history items from scratch.
    """

    @classmethod
    def get_activity(cls, barrier, use_cache=False):
        history = cls.get_barrier_history(
            barrier_id=barrier.pk,
            fields=["archived", "priority", "status"],
            use_cache=use_cache,
        )
        history += cls.get_economic_assessment_history(
            barrier_id=barrier.pk,
            fields=("rating",),
            use_cache=use_cache,
        )
        history += cls.get_economic_impact_assessment_history(
            barrier_id=barrier.pk,
            fields=("impact",),
            use_cache=use_cache,
        )
        history += cls.get_resolvability_assessment_history(
            barrier_id=barrier.pk,
            fields=("time_to_resolve",),
            use_cache=use_cache,
        )
        history += cls.get_strategic_assessment_history(
            barrier_id=barrier.pk,
            fields=("scale",),
            use_cache=use_cache,
        )
        return history

    @classmethod
    def get_public_activity(cls, public_barrier, use_cache=False):
        history_items = HistoryManager.get_public_barrier_history(
            barrier_id=public_barrier.barrier_id,
            start_date=public_barrier.created_on + datetime.timedelta(seconds=1),
            use_cache=use_cache,
        )
        return history_items

    @classmethod
    def get_full_history(cls, barrier, ignore_creation_items=False, use_cache=False):
        if use_cache:
            return cls.get_full_history_cached(barrier, ignore_creation_items)

        if ignore_creation_items:
            start_date = barrier.reported_on
        else:
            start_date = None

        v2_barrier_history = Barrier.get_history(barrier_id=barrier.pk)
        v2_programme_fund_history = ProgrammeFundProgressUpdate.get_history(
            barrier_id=barrier.pk
        )
        v2_top_priority_summary_history = BarrierTopPrioritySummary.get_history(
            barrier_id=barrier.pk
        )

        v2_action_plan_history = ActionPlan.get_history(barrier_id=barrier.pk)
        v2_action_plan_task_history = ActionPlanTask.get_history(barrier_id=barrier.pk)
        v2_action_plan_milestone_history = ActionPlanMilestone.get_history(
            barrier_id=barrier.pk
        )

        v2_history = enrich_full_history(
            barrier_history=v2_barrier_history,
            programme_fund_history=v2_programme_fund_history,
            top_priority_summary_history=v2_top_priority_summary_history,
            action_plan_history=v2_action_plan_history,
            action_plan_task_history=v2_action_plan_task_history,
            action_plan_milestone_history=v2_action_plan_milestone_history,
        )

        history = convert_v2_history_to_legacy_object(v2_history)

        # TODO: Deprecate legacy history implementation for V2
        # history += cls.get_action_plans_history(barrier.pk, start_date=start_date)
        history += cls.get_notes_history(barrier.pk, start_date=start_date)
        history += cls.get_delivery_confidence_history(
            barrier.pk, start_date=start_date
        )
        history += cls.get_economic_assessment_history(
            barrier.pk, start_date=start_date
        )
        history += cls.get_economic_impact_assessment_history(
            barrier.pk, start_date=start_date
        )
        history += cls.get_resolvability_assessment_history(
            barrier.pk, start_date=start_date
        )
        history += cls.get_strategic_assessment_history(
            barrier.pk, start_date=start_date
        )
        history += cls.get_wto_history(barrier.pk, start_date=start_date)

        if start_date:
            history += cls.get_team_history(
                barrier.pk,
                start_date=start_date + datetime.timedelta(seconds=1),
            )
        else:
            history += cls.get_team_history(barrier.pk)

        if barrier.has_public_barrier:
            if ignore_creation_items:
                history += cls.get_public_barrier_history(
                    barrier.pk,
                    start_date=barrier.public_barrier.created_on
                    + datetime.timedelta(seconds=1),
                )
            else:
                history += cls.get_public_barrier_history(barrier.pk)
            history += cls.get_public_barrier_notes_history(barrier.pk)

        return history

    @classmethod
    def get_full_history_cached(cls, barrier, ignore_creation_items=False):
        cached_history_items = CachedHistoryItem.objects.filter(barrier_id=barrier.pk)
        if ignore_creation_items:
            cached_history_items = cached_history_items.filter(
                date__gt=barrier.reported_on + datetime.timedelta(seconds=1),
            )
            if barrier.has_public_barrier:
                cached_history_items = cached_history_items.exclude(
                    model="public_barrier",
                    date__lt=barrier.public_barrier.created_on
                    + datetime.timedelta(seconds=1),
                )

        history_items = []
        for item in cached_history_items:
            history_item = item.as_history_item()
            if history_item.is_valid():
                history_items.append(item.as_history_item())
        return history_items

    @classmethod
    def get_cached_history_items(cls, barrier_id, model, fields=(), start_date=None):
        queryset = CachedHistoryItem.objects.filter(
            barrier_id=barrier_id,
            model=model,
        )
        if start_date:
            queryset = queryset.filter(date__gt=start_date)
        if fields:
            queryset = queryset.filter(field__in=fields)
        return [item.as_history_item() for item in queryset]

    @classmethod
    def get_economic_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="economic_assessment",
                fields=fields,
                start_date=start_date,
            )

        return EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_economic_impact_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="economic_impact_assessment",
                fields=fields,
                start_date=start_date,
            )

        return EconomicImpactAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_barrier_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="barrier",
                fields=fields,
                start_date=start_date,
            )

        return BarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_notes_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="note",
                fields=fields,
                start_date=start_date,
            )

        return NoteHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_delivery_confidence_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):

        return DeliveryConfidenceHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_public_barrier_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="public_barrier",
                fields=fields,
                start_date=start_date,
            )

        return PublicBarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_public_barrier_notes_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="public_barrier_note",
                fields=fields,
                start_date=start_date,
            )

        return PublicBarrierNoteHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_resolvability_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="resolvability_assessment",
                fields=fields,
                start_date=start_date,
            )

        return ResolvabilityAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_strategic_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="strategic_assessment",
                fields=fields,
                start_date=start_date,
            )

        return StrategicAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_team_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="team_member",
                fields=fields,
                start_date=start_date,
            )

        return TeamMemberHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_wto_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="wto",
                fields=fields,
                start_date=start_date,
            )

        return WTOHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )
