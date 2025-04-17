import datetime

import pytest
from django.utils import timezone

from api.barrier_downloads.serializers import CsvDownloadSerializer
from api.barrier_downloads.service import get_queryset
from api.barriers.models import (
    BarrierCommodity,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    EstimatedResolutionDateRequest,
)
from api.collaboration.models import TeamMember
from api.core.test_utils import create_test_user
from api.metadata.constants import PROGRESS_UPDATE_CHOICES, OrganisationType
from api.metadata.models import BarrierPriority
from tests.barriers.factories import BarrierFactory, CommodityFactory
from tests.history.factories import ProgrammeFundProgressUpdateFactory
from tests.metadata.factories import BarrierTagFactory, OrganisationFactory

pytestmark = [pytest.mark.django_db]


EXPECTED_QUERY_COUNT = 13  # 1 + 11 m2m prefetch


def test_csv_serializer_query_count(django_assert_num_queries):
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

    b1 = BarrierFactory(summary="Summ1", created_by=user2, estimated_resolution_date=datetime.datetime.now())
    b2 = BarrierFactory(
        summary="Summ2",
        priority=BarrierPriority.objects.last(),
        sectors_affected=True,
        sectors=["af959812-6095-e211-a939-e4115bead28a"],
        created_by=user,
    )
    b1.organisations.add(o1)
    b2.organisations.add(o2)
    b2.tags.add(tag1)
    b2.tags.add(tag2)
    b1.tags.add(tag1)
    TeamMember.objects.create(barrier=b2, user=user, role="Owner")
    TeamMember.objects.create(barrier=b2, user=user2, role="Contributor")
    TeamMember.objects.create(barrier=b1, role="Owner")

    EstimatedResolutionDateRequest.objects.create(barrier=b1, reason="Hello", status="NEEDS_REVIEW")

    BarrierProgressUpdate.objects.create(
        barrier=b2,
        status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
        update="My update",
        next_steps="This next step",
        created_on=timezone.now(),
    )

    ProgrammeFundProgressUpdateFactory(
        barrier=b2,
        milestones_and_deliverables="m&d1",
        created_on=timezone.now(),
        created_by=user,
    )
    ProgrammeFundProgressUpdateFactory(
        barrier=b2,
        milestones_and_deliverables="m&d2",
        created_on=timezone.now(),
        created_by=user,
    )
    ProgrammeFundProgressUpdateFactory(
        barrier=b1,
        milestones_and_deliverables="m&d2",
        created_on=timezone.now(),
        created_by=user,
    )

    BarrierNextStepItem.objects.create(
        barrier=b2, next_step_item="Test1", completion_date=timezone.now()
    )
    BarrierNextStepItem.objects.create(
        barrier=b2, next_step_item="Test2", completion_date=timezone.now()
    )

    BarrierCommodity.objects.create(barrier=b2, commodity=commodity, code="Test1")

    queryset = get_queryset([b1.id, b2.id])

    with django_assert_num_queries(EXPECTED_QUERY_COUNT):
        s = CsvDownloadSerializer(queryset, many=True).data

    assert len(s) == 2

    b3 = BarrierFactory(summary="Summ1", created_by=user)

    queryset = get_queryset([b1.id, b2.id, b3.id])

    with django_assert_num_queries(EXPECTED_QUERY_COUNT):
        # Query count remains constant even with more barriers
        s = CsvDownloadSerializer(queryset, many=True).data

    assert len(s) == 3
    assert s[0]["barrier_owner"] is None
    assert s[0]["erd_request_status"] == "None"
    assert s[1]["barrier_owner"] == "Hey Siri"
    assert s[1]["progress_update_next_steps"] == "This next step"
    assert s[1]["erd_request_status"] == "None"
    assert s[2]["barrier_owner"] is None
    assert s[2]["erd_request_status"] == "Delete pending"
