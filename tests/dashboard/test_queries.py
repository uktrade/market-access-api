from datetime import date, datetime, timedelta

import freezegun
import pytest
from factory.fuzzy import FuzzyDate

from api.barriers.models import Barrier
from api.core.test_utils import create_test_user
from api.dashboard.service import get_counts, get_financial_year_dates
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT,
    PRIORITY_LEVELS,
    TOP_PRIORITY_BARRIER_STATUS,
    BarrierStatus,
)
from tests.assessment.factories import EconomicImpactAssessmentFactory
from tests.barriers.factories import BarrierFactory, ReportFactory

freezegun.configure(extend_ignore_list=["transformers"])


pytestmark = [pytest.mark.django_db]


@pytest.fixture
def users():
    return [
        create_test_user(
            first_name="Test1",
            last_name="Last1",
            email="Test1@Userii.com",
            username="Name1",
        ),
        create_test_user(
            first_name="Test2",
            last_name="Last2",
            email="Test2@Userii.com",
            username="Name2",
        ),
        create_test_user(
            first_name="Test3",
            last_name="Last3",
            email="Test3@Userii.com",
            username="Name3",
        ),
    ]


@pytest.fixture
def barrier_factory(users):
    start_date, end_date, previous_start_date, previous_end_date = (
        get_financial_year_dates()
    )

    def func(estimated_resolution_date=None):
        if not estimated_resolution_date:
            fuzzy_date = FuzzyDate(
                start_date=start_date,
                end_date=start_date + timedelta(days=45),
            ).evaluate(2, None, False)
            estimated_resolution_date = date(
                year=fuzzy_date.year, month=fuzzy_date.month, day=fuzzy_date.day
            )

        return [
            ReportFactory(
                created_by=users[0], estimated_resolution_date=estimated_resolution_date
            ),
            BarrierFactory(
                created_by=users[0], estimated_resolution_date=estimated_resolution_date
            ),
            BarrierFactory(
                created_by=users[0], estimated_resolution_date=estimated_resolution_date
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.OPEN_IN_PROGRESS,
                top_priority_status=TOP_PRIORITY_BARRIER_STATUS.APPROVED,
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.OPEN_IN_PROGRESS,
                top_priority_status=TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.OPEN_IN_PROGRESS,
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.DORMANT,
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.DORMANT,
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.RESOLVED_IN_PART,
                status_date=datetime.now(),
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.RESOLVED_IN_FULL,
                status_date=datetime.now(),
                estimated_resolution_date=estimated_resolution_date,
            ),
            BarrierFactory(
                created_by=users[0],
                status=BarrierStatus.OPEN_IN_PROGRESS,
                priority_level=PRIORITY_LEVELS.OVERSEAS,
                estimated_resolution_date=estimated_resolution_date,
            ),
        ]

    return func


def test_get_counts_full_schema(users):
    ts = datetime.now()
    financial_dates = get_financial_year_dates()
    BarrierFactory(created_by=users[0], estimated_resolution_date=ts)
    qs = Barrier.objects.all()
    counts = get_counts(qs, users[0])

    assert counts == {
        "barrier_value_chart": {
            "estimated_barriers_value": None,
            "resolved_barriers_value": None,
        },
        "barriers": {
            "open": 0,
            "overseas_delivery": 0,
            "paused": 0,
            "pb100": 0,
            "resolved": 0,
            "total": 1,
        },
        "barriers_by_status_chart": {"labels": [], "series": []},
        "barriers_current_year": {
            "open": 0,
            "overseas_delivery": 0,
            "paused": 0,
            "pb100": 0,
            "resolved": 0,
            "total": 1,
        },
        "financial_year": {
            "current_start": financial_dates[0],
            "current_end": financial_dates[1],
            "previous_start": financial_dates[2],
            "previous_end": financial_dates[3],
        },
        "reports": 0,
        "total_value_chart": {
            "open_barriers_value": None,
            "resolved_barriers_value": None,
        },
        "user_counts": {
            "user_barrier_count": 1,
            "user_open_barrier_count": 0,
            "user_report_count": 0,
        },
    }


def test_get_financial_year_meta_before_april():
    ts = datetime(year=2014, month=3, day=31)
    with freezegun.freeze_time(ts):
        start_date, end_date, previous_start_date, previous_end_date = (
            get_financial_year_dates()
        )

    assert start_date.year == ts.year - 1
    assert end_date.year == ts.year
    assert previous_end_date.year == ts.year - 1
    assert previous_start_date.year == ts.year - 2


def test_get_financial_year_meta_after_april():
    ts = datetime(year=2014, month=4, day=1)
    with freezegun.freeze_time(ts):
        start_date, end_date, previous_start_date, previous_end_date = (
            get_financial_year_dates()
        )

    assert start_date.year == ts.year
    assert end_date.year == ts.year + 1
    assert previous_end_date.year == ts.year
    assert previous_start_date.year == ts.year - 1


def test_get_user_counts(users):
    ReportFactory(created_by=users[0])
    BarrierFactory(created_by=users[0])
    BarrierFactory(created_by=users[0])
    BarrierFactory(created_by=users[0], status=2)
    BarrierFactory(created_by=users[1])
    ReportFactory(created_by=users[2])

    qs = Barrier.objects.all()

    assert get_counts(qs, users[0])["user_counts"] == {
        "user_barrier_count": 3,  # Report not included?
        "user_open_barrier_count": 1,
        "user_report_count": 1,
    }

    assert get_counts(qs, users[1])["user_counts"] == {
        "user_barrier_count": 1,
        "user_open_barrier_count": 0,
        "user_report_count": 0,
    }

    assert get_counts(qs, users[2])["user_counts"] == {
        "user_barrier_count": 0,
        "user_open_barrier_count": 0,
        "user_report_count": 1,
    }


def test_get_barriers(users, barrier_factory):
    barrier_factory()
    qs = Barrier.objects.all()

    barriers = get_counts(qs, users[0])["barriers"]

    assert barriers == {
        "open": 5,
        "overseas_delivery": 1,
        "paused": 2,
        "pb100": 2,
        "resolved": 1,
        "total": 11,
    }


def test_get_barriers_old_date(users, barrier_factory):
    barrier_factory(estimated_resolution_date=datetime.now() - timedelta(days=2 * 365))
    qs = Barrier.objects.all()

    barriers = get_counts(qs, users[0])["barriers"]

    assert barriers == {
        "open": 5,
        "overseas_delivery": 1,
        "paused": 2,
        "pb100": 2,
        "resolved": 1,
        "total": 11,
    }


def test_get_barriers_current_year(users, barrier_factory):
    barrier_factory()
    qs = Barrier.objects.all()

    barriers_current_year = get_counts(qs, users[0])["barriers_current_year"]

    assert barriers_current_year == {
        "open": 5,
        "overseas_delivery": 1,
        "paused": 2,
        "pb100": 2,
        "resolved": 1,
        "total": 11,
    }


@pytest.mark.parametrize(
    "date",
    [
        get_financial_year_dates()[0],
        get_financial_year_dates()[1],
    ],
)
def test_get_barriers_current_financial_year(users, barrier_factory, date):
    barrier_factory(estimated_resolution_date=date)
    qs = Barrier.objects.all()

    barriers_current_year = get_counts(qs, users[0])["barriers_current_year"]

    assert barriers_current_year == {
        "open": 5,
        "overseas_delivery": 1,
        "paused": 2,
        "pb100": 2,
        "resolved": 1,
        "total": 11,
    }


def test_barriers_by_status_chart_empty(users, barrier_factory):
    barrier_factory()
    qs = Barrier.objects.all()

    barriers_by_status_chart = get_counts(qs, users[0])["barriers_by_status_chart"]

    assert barriers_by_status_chart == {"labels": [], "series": []}


def test_barriers_by_status_chart(users, barrier_factory):
    barriers = barrier_factory()
    assessment_impacts = list(ECONOMIC_ASSESSMENT_IMPACT)
    for i, barrier in enumerate(barriers):
        EconomicImpactAssessmentFactory(
            barrier=barrier, impact=assessment_impacts[i][0]
        )
    qs = Barrier.objects.all()

    barriers_by_status_chart = get_counts(qs, users[0])["barriers_by_status_chart"]

    assert barriers_by_status_chart == {
        "labels": ["Resolved: In part", "Dormant", "Resolved: In full", "Open"],
        "series": [5500000, 8000000, 8500000, 57260000],
    }


@pytest.mark.parametrize(
    "status",
    [
        BarrierStatus.OPEN_IN_PROGRESS,
        BarrierStatus.DORMANT,
        BarrierStatus.RESOLVED_IN_FULL,
        BarrierStatus.RESOLVED_IN_PART,
    ],
)
def test_barrier_by_status_by_labal(users, status):
    assessment_impacts = list(ECONOMIC_ASSESSMENT_IMPACT)
    barrier1 = BarrierFactory(status=status, status_date=datetime.now())
    barrier2 = BarrierFactory(status=status, status_date=datetime.now())
    EconomicImpactAssessmentFactory(barrier=barrier1, impact=assessment_impacts[0][0])
    EconomicImpactAssessmentFactory(barrier=barrier2, impact=assessment_impacts[1][0])
    qs = Barrier.objects.all()

    barriers_by_status_chart = get_counts(qs, users[0])["barriers_by_status_chart"]

    index = None
    for i, label in enumerate(barriers_by_status_chart["labels"]):
        if label == dict(BarrierStatus.choices)[status]:
            index = i
            break

    assert barriers_by_status_chart["series"][index] == 60000
    assert (
        barriers_by_status_chart["labels"][index] == dict(BarrierStatus.choices)[status]
    )


def test_total_value_chart(users, barrier_factory):
    barriers = barrier_factory()
    assessment_impacts = list(ECONOMIC_ASSESSMENT_IMPACT)
    for i, barrier in enumerate(barriers):
        EconomicImpactAssessmentFactory(
            barrier=barrier, impact=assessment_impacts[i][0]
        )
    qs = Barrier.objects.all()

    total_value_chart = get_counts(qs, users[0])["total_value_chart"]

    assert total_value_chart == {
        "resolved_barriers_value": 14000000,
        "open_barriers_value": 57260000,
    }


def test_barrier_value_chart(users, barrier_factory):
    barriers = barrier_factory()
    assessment_impacts = list(ECONOMIC_ASSESSMENT_IMPACT)
    for i, barrier in enumerate(barriers):
        EconomicImpactAssessmentFactory(
            barrier=barrier, impact=assessment_impacts[i][0]
        )
    qs = Barrier.objects.all()

    barrier_value_chart = get_counts(qs, users[0])["barrier_value_chart"]

    assert barrier_value_chart == {
        "resolved_barriers_value": 14000000,
        "estimated_barriers_value": 57260000,
    }
