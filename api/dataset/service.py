from typing import Dict, Callable, Tuple

from rest_framework.pagination import CursorPagination

from api.action_plans.models import ActionPlan
from api.assessment.models import EconomicAssessment
from api.barriers.models import Barrier, ProgrammeFundProgressUpdate, BarrierTopPrioritySummary, BarrierNextStepItem
from api.dataset import table_schemas


def get_barrier_next_steps_history():
    return BarrierNextStepItem.history.all()


def get_barrier_economic_assessment():
    return EconomicAssessment.history.all()


def get_barrier_action_plan_history():
    return ActionPlan.history.all()


def get_barrier_history():
    return Barrier.history.all()


def get_programme_fund_history():
    return ProgrammeFundProgressUpdate.history.all()


def get_barrier_top_priority_summary():
    return BarrierTopPrioritySummary.history.all()


DATASET_META: Dict[str, Tuple[Callable, Dict, Tuple]] = {
    table_schemas.BARRIER_HISTORY["name"]: (
        get_barrier_history,                    # queryset
        table_schemas.BARRIER_HISTORY,          # schema
        ("history_date",)                       # pagination ordering
    ),
    table_schemas.PROGRAMME_FUND_PROGRESS_UPDATE_HISTORY["name"]: (
        get_programme_fund_history,
        table_schemas.PROGRAMME_FUND_PROGRESS_UPDATE_HISTORY,
        ("history_date",)
    ),
    table_schemas.TOP_PRIORITY_SUMMARY_HISTORY["name"]: (
        get_barrier_top_priority_summary,
        table_schemas.TOP_PRIORITY_SUMMARY_HISTORY,
        ("history_date",)
    ),
    table_schemas.NEXT_STEP_HISTORY["name"]: (
        get_barrier_next_steps_history,
        table_schemas.NEXT_STEP_HISTORY,
        ("history_date",)
    ),
    table_schemas.ACTION_PLAN_HISTORY["name"]: (
        get_barrier_action_plan_history,
        table_schemas.ACTION_PLAN_HISTORY,
        ("history_date",)
    ),
    table_schemas.ECONOMIC_ASSESSMENT_HISTORY["name"]: (
        get_barrier_economic_assessment,
        table_schemas.ECONOMIC_ASSESSMENT_HISTORY,
        ("history_date",)
    ),
}


def get_paginator(ordering):
    paginator = CursorPagination()
    paginator.page_size = 1000
    paginator.ordering = ordering

    return paginator


def process_request(request):

    table = request.GET.get('table')
    qs_generator, table_schema, ordering = DATASET_META[table]
    qs = qs_generator().values(*[col["name"] for col in table_schema["columns"]])

    paginator = get_paginator(ordering)
    page = paginator.paginate_queryset(qs, request)
    next = paginator.get_next_link()

    return {
        'table': table,
        'rows': page,
        'next': next
    }
