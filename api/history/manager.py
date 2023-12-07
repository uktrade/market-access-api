import datetime

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
from api.history.factories.action_plans import (
    ActionPlanHistoryFactory,
    ActionPlanMilestoneHistoryFactory,
    ActionPlanTaskHistoryFactory,
)
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

        v2_history = enrich_full_history(
            barrier_history=v2_barrier_history,
            programme_fund_history=v2_programme_fund_history,
            top_priority_summary_history=v2_top_priority_summary_history,
        )

        history = convert_v2_history_to_legacy_object(v2_history)

        # TODO: Deprecate legacy history implementation for V2
        history += cls.get_action_plans_history(barrier.pk, start_date=start_date)
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
    def get_economic_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        return EconomicAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_economic_impact_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        return EconomicImpactAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_barrier_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        return BarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_action_plans_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):

        return [
            *ActionPlanHistoryFactory.get_history_items(
                barrier_id=barrier_id,
                fields=fields,
                start_date=start_date,
            ),
            *ActionPlanTaskHistoryFactory.get_history_items(
                barrier_id=barrier_id,
                fields=fields,
                start_date=start_date,
            ),
            *ActionPlanMilestoneHistoryFactory.get_history_items(
                barrier_id=barrier_id,
                fields=fields,
                start_date=start_date,
            ),
        ]

    @classmethod
    def get_notes_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
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
        return PublicBarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_public_barrier_notes_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        return PublicBarrierNoteHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_resolvability_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        return ResolvabilityAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_strategic_assessment_history(
        cls, barrier_id, fields=(), start_date=None, use_cache=False
    ):
        return StrategicAssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_team_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        return TeamMemberHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_wto_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        return WTOHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )
