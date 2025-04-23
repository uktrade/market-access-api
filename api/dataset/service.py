from rest_framework.pagination import CursorPagination

from api.barriers.models import Barrier
from api.history.v2.service import get_history_changes


def get_paginator(ordering):
    paginator = CursorPagination()
    paginator.page_size = 5000
    paginator.ordering = ordering

    return paginator


FIELDS = [
    "archived",
    "archived_reason",
    "archived_explanation",
    "unarchived_reason",
    "country",
    "trading_bloc",
    "caused_by_trading_bloc",
    "admin_areas",
    "commercial_value",
    "commercial_value_explanation",
    "companies",
    "economic_assessment_eligibility",
    "economic_assessment_eligibility_summary",
    "estimated_resolution_date",
    "start_date",
    "is_summary_sensitive",
    "main_sector",
    "priority_level",
    "priority__code",
    "priority_summary",
    "product",
    "public_eligibility_summary",
    "sectors",
    "all_sectors",
    "source",
    "other_source",
    "status",
    "status_date",
    "status_summary",
    "sub_status",
    "sub_status_other",
    "summary",
    "term",
    "title",
    "trade_category",
    "trade_direction",
    "top_priority_status",
    "top_priority_rejection_summary",
    "draft",
    # m2m - seperate
    "tags_cache",  # needs cache
    "organisations_cache",  # Needs cache
    "commodities_cache",  # Needs cache
    "categories_cache",  # Needs cache
    "policy_teams_cache",  # Needs cache
]


def get_barrier_history(request):
    qs = Barrier.history.all()

    qs = qs.values(
        *["id", "history_date", "history_user__id", "history_user__username"] + FIELDS
    )

    paginator = get_paginator(("id", "history_date"))
    page = paginator.paginate_queryset(qs, request)
    next = paginator.get_next_link()

    history = get_history_changes(
        page, model="barrier", fields=FIELDS, track_first_item=False, primary_key="id"
    )

    for h in history:
        h["barrier_id"] = h["id"]
        h["user_id"] = h["user"]["id"] if h["user"] else None
        h["user_name"] = h["user"]["name"] if h["user"] else None
        del h["user"]
        del h["id"]

    return {"results": history, "next": next}
