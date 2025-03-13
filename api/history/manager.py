import datetime

from api.action_plans.models import ActionPlan, ActionPlanMilestone, ActionPlanTask
from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    PreliminaryAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    BarrierTopPrioritySummary,
    EstimatedResolutionDateRequest,
    ProgrammeFundProgressUpdate,
    PublicBarrier,
)
from api.collaboration.models import TeamMember
from api.history.factories import PublicBarrierHistoryFactory
from api.history.v2.enrichment import (
    enrich_impact,
    enrich_preliminary_assessment,
    enrich_scale_history,
    enrich_status,
    enrich_time_to_resolve,
)
from api.history.v2.service import (
    FieldMapping,
    convert_v2_history_to_legacy_object,
    enrich_full_history,
)
from api.wto.models import WTOProfile


class HistoryManager:
    """
    Used for querying history items.

    Can either query the cache or generate history items from scratch.
    """

    @classmethod
    def get_activity(cls, barrier):
        v2_barrier_history = Barrier.get_history(
            barrier_id=barrier.pk,
            fields=[
                [
                    "archived",
                    "archived_reason",
                    "archived_explanation",
                    "unarchived_reason",
                ],
                [FieldMapping("priority__code", "priority"), "priority_summary"],
                [
                    "status",
                    "status_date",
                    "status_summary",
                    "sub_status",
                    "sub_status_other",
                ],
            ],
            track_first_item=True,
        )

        v2_preliminary_assessment_history = PreliminaryAssessment.get_history(
            barrier_id=barrier.pk,
        )
        v2_economic_assessment_history = EconomicAssessment.get_history(
            barrier_id=barrier.pk, fields=["rating"]
        )
        v2_resolvability_assessment_history = ResolvabilityAssessment.get_history(
            barrier_id=barrier.pk, fields=["time_to_resolve"]
        )
        v2_economic_impact_assessment_history = EconomicImpactAssessment.get_history(
            barrier_id=barrier.pk, fields=["impact"]
        )
        v2_strategic_assessment_history = StrategicAssessment.get_history(
            barrier_id=barrier.pk, fields=["scale"]
        )
        enrich_status(v2_barrier_history)
        enrich_preliminary_assessment(v2_preliminary_assessment_history)
        history = convert_v2_history_to_legacy_object(v2_barrier_history)

        enrich_scale_history(v2_strategic_assessment_history)
        enrich_impact(v2_strategic_assessment_history)
        enrich_time_to_resolve(v2_strategic_assessment_history)

        history += convert_v2_history_to_legacy_object(
            v2_economic_assessment_history
            + v2_resolvability_assessment_history
            + v2_economic_impact_assessment_history
            + v2_strategic_assessment_history
        )

        return history

    @classmethod
    def get_full_history(cls, barrier, ignore_creation_items=False):
        if ignore_creation_items:
            start_date = barrier.reported_on
        else:
            start_date = None

        v2_barrier_history = Barrier.get_history(barrier_id=barrier.pk)
        v2_preliminary_assessment_history = PreliminaryAssessment.get_history(
            barrier_id=barrier.pk,
        )
        v2_programme_fund_history = ProgrammeFundProgressUpdate.get_history(
            barrier_id=barrier.pk
        )
        v2_top_priority_summary_history = BarrierTopPrioritySummary.get_history(
            barrier_id=barrier.pk
        )
        v2_economic_assessment_history = EconomicAssessment.get_history(
            barrier_id=barrier.pk
        )
        v2_economic_impact_assessment_history = EconomicImpactAssessment.get_history(
            barrier_id=barrier.pk
        )
        v2_resolvability_assessment_history = ResolvabilityAssessment.get_history(
            barrier_id=barrier.pk
        )
        v2_strategic_assessment_history = StrategicAssessment.get_history(
            barrier_id=barrier.pk
        )
        v2_action_plan_history = ActionPlan.get_history(barrier_id=barrier.pk)
        v2_action_plan_task_history = ActionPlanTask.get_history(barrier_id=barrier.pk)
        v2_action_plan_milestone_history = ActionPlanMilestone.get_history(
            barrier_id=barrier.pk
        )

        v2_delivery_confidence_history = BarrierProgressUpdate.get_history(
            barrier_id=barrier.pk
        )

        v2_wto_history = WTOProfile.get_history(barrier_id=barrier.pk)

        v2_team_member_history = TeamMember.get_history(barrier_id=barrier.pk)

        v2_next_step_item_history = BarrierNextStepItem.get_history(
            barrier_id=barrier.pk
        )

        v2_public_barrier_history = None

        if barrier.has_public_barrier:
            v2_public_barrier_history = PublicBarrier.get_history(barrier.pk)

        v2_estimated_resolution_date_request_history = (
            EstimatedResolutionDateRequest.get_history(barrier_id=barrier.pk)
        )
        v2_history = enrich_full_history(
            barrier_history=v2_barrier_history,
            preliminary_assessment_history=v2_preliminary_assessment_history,
            programme_fund_history=v2_programme_fund_history,
            top_priority_summary_history=v2_top_priority_summary_history,
            wto_history=v2_wto_history,
            team_member_history=v2_team_member_history,
            public_barrier_history=v2_public_barrier_history,
            economic_assessment_history=v2_economic_assessment_history,
            economic_impact_assessment_history=v2_economic_impact_assessment_history,
            resolvability_assessment_history=v2_resolvability_assessment_history,
            strategic_assessment_history=v2_strategic_assessment_history,
            action_plan_history=v2_action_plan_history,
            action_plan_task_history=v2_action_plan_task_history,
            action_plan_milestone_history=v2_action_plan_milestone_history,
            delivery_confidence_history=v2_delivery_confidence_history,
            next_step_item_history=v2_next_step_item_history,
            estimated_resolution_date_request_history=v2_estimated_resolution_date_request_history,
        )

        history = convert_v2_history_to_legacy_object(v2_history)

        return history

    @classmethod
    def get_public_activity(cls, public_barrier):
        history_items = HistoryManager.get_public_barrier_history(
            barrier_id=public_barrier.barrier_id,
            start_date=public_barrier.created_on + datetime.timedelta(seconds=1),
        )
        return history_items

    @classmethod
    def get_public_barrier_history(cls, barrier_id, fields=(), start_date=None):
        return PublicBarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )
