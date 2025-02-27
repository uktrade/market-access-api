import logging
from datetime import date, datetime, timedelta

import pytz
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    DateTimeField,
    Exists,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Concat, Greatest

from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    EstimatedResolutionDateRequest,
    ProgrammeFundProgressUpdate,
)
from api.collaboration.models import TeamMember
from api.dashboard import tasks
from api.interactions.models import Mention
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC_LOOKUP,
    GOVERNMENT_ORGANISATION_TYPES,
    TOP_PRIORITY_BARRIER_STATUS,
    BarrierStatus,
)

logger = logging.getLogger(__name__)


def get_financial_year_dates():
    today = date.today()
    if today.month < 4:
        start_date = date(year=today.year - 1, month=4, day=1)
    else:
        start_date = date(year=today.year, month=4, day=1)

    end_date = date(year=start_date.year + 1, month=3, day=31)
    previous_start_date = date(year=start_date.year - 1, month=4, day=1)
    previous_end_date = date(year=start_date.year, month=3, day=31)

    return start_date, end_date, previous_start_date, previous_end_date


def get_counts(qs, user):
    current_year_start, current_year_end, previous_year_start, previous_year_end = (
        get_financial_year_dates()
    )

    if not user.is_anonymous:
        user_barrier_count = Barrier.barriers.filter(created_by=user).count()
        user_report_count = Barrier.reports.filter(created_by=user).count()
        user_open_barrier_count = Barrier.barriers.filter(
            created_by=user, status=2
        ).count()

    when_assessment = [
        When(valuation_assessments__impact=k, then=Value(v))
        for k, v in ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC_LOOKUP
    ]

    # Resolved vs Estimated barriers values chart
    resolved_valuations = (
        qs.filter(
            Q(
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end,
                ]
            )
            | Q(
                status_date__range=[
                    current_year_start,
                    current_year_end,
                ]
            ),
            Q(status=4) | Q(status=3),
            valuation_assessments__archived=False,
        )
        .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
        .aggregate(total=Sum("numeric_value"))
    )

    resolved_barrier_value = resolved_valuations["total"]

    estimated_valuations = (
        qs.filter(
            Q(
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end + timedelta(days=1),
                ]
            )
            | Q(
                status_date__range=[
                    current_year_start,
                    current_year_end + timedelta(days=1),
                ]
            ),
            Q(status=1) | Q(status=2),
            valuation_assessments__archived=False,
        )
        .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
        .aggregate(total=Sum("numeric_value"))
    )

    estimated_barrier_value = estimated_valuations["total"]

    # Total resolved barriers vs open barriers value chart

    resolved_barriers = (
        qs.filter(
            Q(status=4) | Q(status=3),
            valuation_assessments__archived=False,
        )
        .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
        .aggregate(total=Sum("numeric_value"))
    )

    total_resolved_barriers = resolved_barriers["total"]

    open_barriers = (
        qs.filter(
            Q(status=1) | Q(status=2),
            valuation_assessments__archived=False,
        )
        .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
        .aggregate(total=Sum("numeric_value"))
    )

    open_barriers_value = open_barriers["total"]

    # Open barriers by status
    whens = [When(status=k, then=Value(v)) for k, v in BarrierStatus.choices]

    barrier_by_status = (
        qs.filter(
            valuation_assessments__archived=False,
        )
        .annotate(status_display=Case(*whens, output_field=CharField()))
        .annotate(numeric_value=Case(*when_assessment, output_field=IntegerField()))
        .values("status_display")
        .annotate(total=Sum("numeric_value"))
        .order_by()
    )

    status_labels = []
    status_data = []

    barrier_by_status = sorted(barrier_by_status, key=lambda x: x["total"])

    for series in barrier_by_status:
        status_labels.append(series["status_display"])
        status_data.append(series["total"])

    # TODO for status filter might need to consider status dates as well as ERD
    return {
        "financial_year": {
            "current_start": current_year_start,
            "current_end": current_year_end,
            "previous_start": previous_year_start,
            "previous_end": previous_year_end,
        },
        "barriers": {
            "total": qs.count(),
            "open": qs.filter(status__in=[2, 3]).count(),
            "paused": qs.filter(status=5).count(),
            "resolved": qs.filter(status=4).count(),
            "pb100": qs.filter(
                top_priority_status__in=["APPROVED", "REMOVAL_PENDING"],
                status__in=[2, 3],
            ).count(),
            "overseas_delivery": qs.filter(
                priority_level="OVERSEAS", status__in=[2, 3]
            ).count(),
        },
        "barriers_current_year": {
            "total": qs.filter(
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end,
                ]
            ).count(),
            "open": qs.filter(
                status__in=[2, 3],
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end,
                ],
            ).count(),
            "paused": qs.filter(
                status=5,
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end,
                ],
            ).count(),
            "resolved": qs.filter(
                status=4,
                status_date__range=[
                    current_year_start,
                    current_year_end,
                ],
            ).count(),
            "pb100": qs.filter(
                status__in=[2, 3],
                top_priority_status__in=["APPROVED", "REMOVAL_PENDING"],
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end,
                ],
            ).count(),
            "overseas_delivery": qs.filter(
                status__in=[2, 3],
                priority_level="OVERSEAS",
                estimated_resolution_date__range=[
                    current_year_start,
                    current_year_end,
                ],
            ).count(),
        },
        "user_counts": {
            "user_barrier_count": user_barrier_count,
            "user_report_count": user_report_count,
            "user_open_barrier_count": user_open_barrier_count,
        },
        "reports": Barrier.reports.count(),
        "barrier_value_chart": {
            "resolved_barriers_value": resolved_barrier_value,
            "estimated_barriers_value": estimated_barrier_value,
        },
        "total_value_chart": {
            "resolved_barriers_value": total_resolved_barriers,
            "open_barriers_value": open_barriers_value,
        },
        "barriers_by_status_chart": {
            "series": status_data,
            "labels": status_labels,
        },
    }


def get_combined_barrier_mention_qs(user):
    return (
        Barrier.objects.filter(
            (
                (Q(barrier_team__user=user) & Q(barrier_team__archived=False))
                | (Q(mention__recipient=user))
            )
            & Q(archived=False)
        )
        .annotate(
            modified_on_union=Case(
                When(
                    Exists(
                        Mention.objects.filter(
                            barrier__id=OuterRef("pk"),
                            recipient=user,
                            created_on__date__gte=(datetime.now() - timedelta(days=30)),
                        )
                    ),
                    then=Greatest(
                        Mention.objects.filter(
                            barrier__id=OuterRef("pk"),
                            recipient=user,
                            created_on__date__gte=(datetime.now() - timedelta(days=30)),
                        )
                        .order_by("-created_on")
                        .values("created_on")[:1],
                        F("modified_on"),
                    ),
                ),
                default=F("modified_on"),
                output_field=DateTimeField(),
            )
        )
        .order_by("-modified_on_union")
        .distinct()
    )


def get_tasks(user):  # noqa
    user_groups = set(user.groups.values_list("name", flat=True))
    fy_start_date, fy_end_date, _, __ = get_financial_year_dates()

    user_is_admin = "Administrator" in user_groups

    barrier_entries = []

    qs = get_combined_barrier_mention_qs(user)

    qs = qs.annotate(
        is_owner=Exists(
            TeamMember.objects.filter(
                barrier=OuterRef("pk"), role=TeamMember.OWNER, user=user, archived=False
            )
        ),
        is_member=Exists(
            TeamMember.objects.filter(barrier=OuterRef("pk"), user=user, archived=False)
        ),
        deadline=ExpressionWrapper(
            F("public_barrier__set_to_allowed_on") + timedelta(days=30),
            output_field=DateTimeField(),
        ),
        full_name=Concat(
            F("modified_by__first_name"),
            Value(" "),
            F("modified_by__last_name"),
            output_field=CharField(),
        ),
        progress_update_modified_on=BarrierProgressUpdate.objects.filter(
            barrier=OuterRef("pk")
        )
        .order_by("-created_on")
        .values("modified_on")[:1],
        has_overdue_next_step=Exists(
            BarrierNextStepItem.objects.filter(
                barrier=OuterRef("pk"),
                status="IN_PROGRESS",
                completion_date__lt=datetime.date(datetime.today()),
            )
        ),
        latest_programme_fund_modified_on=ProgrammeFundProgressUpdate.objects.filter(
            barrier=OuterRef("pk")
        )
        .order_by("-created_on")
        .values("modified_on")[:1],
        has_programme_fund_tag=Exists(
            Barrier.objects.filter(
                pk=OuterRef("pk"), tags__title="Programme Fund - Facilitative Regional"
            )
        ),
        has_goods=Exists(
            Barrier.objects.filter(id=OuterRef("pk"), export_types__name="goods")
        ),
        has_commodities=Exists(
            Barrier.objects.filter(id=OuterRef("pk"), commodities__code__isnull=False)
        ),
        has_government_organisation=Exists(
            Barrier.objects.filter(
                id=OuterRef("pk"),
                organisations__organisation_type__in=GOVERNMENT_ORGANISATION_TYPES,
            )
        ),
        has_estimated_resolution_date_request=Exists(
            Barrier.objects.filter(
                id=OuterRef("pk"),
                estimated_resolution_date_request__status=EstimatedResolutionDateRequest.STATUSES.NEEDS_REVIEW,
            )
        ),
        is_top_priority=ExpressionWrapper(
            Q(top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED)
            | Q(top_priority_status=TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING),
            output_field=BooleanField(),
        ),
    ).values(
        "id",
        "is_member",
        "modified_on_union",
        "title",
        "code",
        "deadline",
        "is_owner",
        "modified_on",
        "full_name",
        "status",
        "top_priority_status",
        "is_top_priority",
        "progress_update_modified_on",
        "has_overdue_next_step",
        "priority_level",
        "has_programme_fund_tag",
        "latest_programme_fund_modified_on",
        "has_goods",
        "has_estimated_resolution_date_request",
        "has_commodities",
        "has_government_organisation",
        "estimated_resolution_date",
        set_to_allowed_on=F("public_barrier__set_to_allowed_on"),
        public_barrier_title=F("public_barrier___title"),
        public_barrier_summary=F("public_barrier___summary"),
        public_view_status=F("public_barrier___public_view_status"),
    )
    mentions = Mention.objects.filter(
        barrier__id__in=[b["id"] for b in qs],
        recipient=user,
        created_on__date__gte=(datetime.now() - timedelta(days=30)),
    ).values(
        "created_on",
        "barrier",
        first_name=F("created_by__first_name"),
        last_name=F("created_by__last_name"),
    )
    mentions_lookup = {m["barrier"]: m for m in mentions}

    for barrier in qs:
        barrier_entry = tasks.create_barrier_entry(barrier)

        if barrier["has_estimated_resolution_date_request"] and user_is_admin:
            task = tasks.create_erd_review_task()
            barrier_entry["task_list"].append(task)

        if barrier["id"] in mentions_lookup:
            mention = mentions_lookup[barrier["id"]]
            task = tasks.create_mentions_task(mention)
            barrier_entry["task_list"].append(task)

        if not barrier["is_member"]:
            # If user isn't part of the barrier team, they should not have any tasks generated
            # for this barrier besides the Mention tasks above.
            if barrier_entry["task_list"]:
                barrier_entries.append(barrier_entry)
            continue

        if barrier["is_owner"] and barrier["public_view_status"] == 20:
            task = tasks.create_editor_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            "Public barrier approver" in user_groups
            and barrier["public_view_status"] == 70
        ):
            task = tasks.create_approver_task(barrier)
            barrier_entry["task_list"].append(task)

        if "Publisher" in user_groups and barrier["public_view_status"] == 30:
            task = tasks.create_publisher_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier["status"] in {1, 2, 3} and barrier["is_top_priority"]:
            task = tasks.create_progress_update_task(barrier)
            if task:
                barrier_entry["task_list"].append(task)

            if barrier["has_overdue_next_step"]:
                task = tasks.create_next_step_task(barrier)
                barrier_entry["task_list"].append(task)

        if (
            barrier["status"] in {1, 2, 3}
            and barrier["priority_level"] == "OVERSEAS"
            and (
                not barrier["progress_update_modified_on"]
                or barrier["progress_update_modified_on"]
                < (datetime.today() - timedelta(days=90)).replace(tzinfo=pytz.UTC)
            )
        ):
            task = tasks.create_overseas_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier["has_programme_fund_tag"] and (
            not barrier["latest_programme_fund_modified_on"]
            or barrier["latest_programme_fund_modified_on"]
            < (datetime.today() - timedelta(days=90)).replace(tzinfo=pytz.UTC)
        ):
            task = tasks.create_programme_fund_update_task(barrier)
            barrier_entry["task_list"].append(task)

        # Barrier missing details
        if (
            barrier["status"] in {1, 2, 3}
            and barrier["has_goods"]
            and not barrier["has_commodities"]
        ):
            task = tasks.create_missing_hs_code_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            barrier["status"] in {1, 2, 3}
            and not barrier["has_government_organisation"]
        ):
            task = tasks.create_missing_gov_org_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            barrier["status"] in {1, 2, 3}
            and barrier["estimated_resolution_date"]
            and not barrier["progress_update_modified_on"]
            and barrier["estimated_resolution_date"] < fy_end_date
            and barrier["estimated_resolution_date"] > fy_start_date
        ):
            task = tasks.create_add_progress_update_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            barrier["status"] in {1, 2, 3}
            and barrier["estimated_resolution_date"]
            and barrier["estimated_resolution_date"] < datetime.today().date()
        ):
            task = tasks.create_overdue_erd_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            barrier["is_owner"]
            and (barrier["is_top_priority"] or barrier["priority_level"] == "OVERSEAS")
            and not barrier["estimated_resolution_date"]
        ):
            task = tasks.create_add_priority_erd_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            barrier["is_owner"]
            and barrier["is_top_priority"]
            and barrier["progress_update_modified_on"]
            and barrier["progress_update_modified_on"]
            < (datetime.now() - timedelta(days=180)).replace(tzinfo=pytz.UTC)
        ):
            task = tasks.create_review_priority_erd_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier_entry["task_list"]:
            barrier_entries.append(barrier_entry)

    return barrier_entries
