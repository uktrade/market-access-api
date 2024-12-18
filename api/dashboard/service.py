from datetime import date, timedelta
from functools import partial

from django.db.models import Case, CharField, IntegerField, Q, Sum, Value, When

from api.barriers.models import Barrier
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC_LOOKUP,
    BarrierStatus,
)


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
