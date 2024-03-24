import pytest
from django.db.models import Prefetch
from django.utils import timezone

from api.barrier_downloads.serializers import CsvDownloadSerializer
from api.barriers.models import Barrier, BarrierProgressUpdate, BarrierNextStepItem, ProgrammeFundProgressUpdate, \
    BarrierCommodity
from api.collaboration.models import TeamMember
from api.core.test_utils import create_test_user
from api.metadata.constants import OrganisationType, PROGRESS_UPDATE_CHOICES
from api.metadata.models import BarrierPriority, Category
from tests.barriers.factories import BarrierFactory, CommodityFactory
from tests.history.factories import ProgrammeFundProgressUpdateFactory
from tests.metadata.factories import BarrierTagFactory, OrganisationFactory

"""
NOTES:

WHy have sectors_affected: bool + sectors: Array in DB? redundant field
"""

pytestmark = [pytest.mark.django_db]


def test_new_serializer(django_assert_num_queries):
    commodity = CommodityFactory()
    o1 = OrganisationFactory(organisation_type=OrganisationType.MINISTERIAL_DEPARTMENTS)
    o2 = OrganisationFactory(organisation_type=OrganisationType.MINISTERIAL_DEPARTMENTS)
    tag1 = BarrierTagFactory()
    tag2 = BarrierTagFactory()
    user = create_test_user(
        first_name="Hey",
        last_name="Siri",
        email="hey@siri.com",
        username="heysiri",
    )
    user2 = create_test_user(
        first_name="Hey2",
        last_name="Siri2",
        email="hey2@siri.com",
        username="heysiri2",
    )

    b1 = BarrierFactory(summary='Summ1', created_by=user2)
    # print(BarrierPriority.objects.all())
    categories = Category.objects.all()
    category1 = categories[0]
    category2 = categories[1]
    b2 = BarrierFactory(
        summary='Summ2',
        priority=BarrierPriority.objects.last(),
        sectors_affected=True,
        sectors=['af959812-6095-e211-a939-e4115bead28a'],
        created_by=user
    )
    b1.organisations.add(o1)
    b2.organisations.add(o2)
    b2.tags.add(tag1)
    b2.tags.add(tag2)
    b1.tags.add(tag1)
    TeamMember.objects.create(
        barrier=b2,  user=user, role="Contributor"
    )
    TeamMember.objects.create(
        barrier=b2, user=user2, role="Contributor"
    )
    b2.categories.add(category1)

    pu1 = BarrierProgressUpdate.objects.create(
        barrier=b2,
        status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
        update="My update",
        next_steps="This next step",
        created_on=timezone.now()
    )

    ProgrammeFundProgressUpdateFactory(barrier=b2, milestones_and_deliverables='m&d1', created_on=timezone.now(), created_by=user)
    ProgrammeFundProgressUpdateFactory(barrier=b2, milestones_and_deliverables='m&d2', created_on=timezone.now(), created_by=user)
    ProgrammeFundProgressUpdateFactory(barrier=b1, milestones_and_deliverables='m&d2', created_on=timezone.now(), created_by=user)

    BarrierNextStepItem.objects.create(barrier=b2, next_step_item="Test1", completion_date=timezone.now())
    BarrierNextStepItem.objects.create(barrier=b2, next_step_item="Test2", completion_date=timezone.now())

    bc = BarrierCommodity.objects.create(barrier=b2, commodity=commodity, code='Test1')

    queryset = (
        Barrier.objects.filter(id__in=[b1.id, b2.id])
        .select_related(
            'priority',
            'created_by',
        )
        .prefetch_related(
            'tags',
            'categories',
            'barrier_team',  # barrier_owner
            'barrier_team__user',  # barrier_owner
            'organisations',  # government_organisations
            Prefetch(
                'progress_updates',
                queryset=BarrierProgressUpdate.objects.order_by("-created_on").all()
            ),
            Prefetch(
                'programme_fund_progress_updates',
                queryset=ProgrammeFundProgressUpdate.objects.select_related('created_by').order_by("-created_on").all()
            ),
            # "progress_updates",  # latest_progress_update, progress_update_message, progress_update_next_steps
            "barrier_commodities",  # commodity_codes
            "public_barrier",
            "economic_assessments",
            "valuation_assessments",
            Prefetch(
                "next_steps_items",
                queryset=BarrierNextStepItem.objects.filter(
                    status="IN_PROGRESS"
                ).order_by("-completion_date")
            )
            # value_to_economy, valuation_assessment_rating, valuation_assessment_midpoint', valuation_assessment_explanation, commercial_value
        )
        .only(
            'id',
            'code',
            'title',
            'is_summary_sensitive',  # used for summary
            'summary',
            'code',  # link
            'status',  # resolved_date
            'sub_status',  # used for status
            'priority',
            'priority__name',
            "progress_updates",
            'country',  # 'overseas_region', "location"
            'trading_bloc',  # 'overseas_region', "location
            'admin_areas',
            'sectors',
            'sectors_affected',
            'all_sectors',
            'product',
            'created_by',
            # 'created_by__first_name',  # reported_by
            # 'created_by__last_name',  # reported_by
            'reported_on',
            # 'barrier_owner',  prefetch_related
            'status_date',  # resolved_date
            'status_summary',
            'modified_on',
            'tags',
            'trade_direction',
            'top_priority_status',  # 'is_resolved_top_priority',
            # 'government_organisations',
            # 'progress_update_message',
            # 'progress_update_next_steps',
            'next_steps_items',
            # 'programme_fund_progress_update_milestones',
            # 'programme_fund_progress_update_expenditure',
            # 'programme_fund_progress_update_date',
            # 'programme_fund_progress_update_author',
            'estimated_resolution_date',
            'proposed_estimated_resolution_date',
            # 'commodity_codes',
            "public_barrier___public_view_status",  # 'public_view_status',
            'public_barrier__changed_since_published',
            'public_barrier___title',
            'public_barrier___summary',
            # 'economic_assessment_rating',  # TODO
            # 'value_to_economy',
            # 'valuation_assessment_rating',
            # 'valuation_assessment_midpoint',
            # 'valuation_assessment_explanation',
            # 'commercial_value',
            "commercial_value"
        )
    )

    # pprint(list(queryset[0].keys()))

    with django_assert_num_queries(13):
        s = CsvDownloadSerializer(queryset, many=True).data
