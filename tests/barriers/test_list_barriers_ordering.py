from datetime import datetime
from itertools import chain

from django.conf import settings
from django.db.models import QuerySet
from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.assessment.models import EconomicImpactAssessment
from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin
from api.metadata.constants import BarrierStatus
from tests.assessment.factories import (
    EconomicAssessmentFactory,
    EconomicImpactAssessmentFactory,
)
from tests.barriers.factories import BarrierFactory


class TestListBarriersOrdering(APITestMixin, APITestCase):
    bahamas = "a25f66a0-5d95-e211-a939-e4115bead28a"
    bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
    spain = "86756b9a-5d95-e211-a939-e4115bead28a"

    countries = (bahamas, bhutan, spain)

    reported_on_dates = (
        datetime(2020, 1, 1, tzinfo=UTC),
        datetime(2020, 2, 1, tzinfo=UTC),
        datetime(2020, 3, 1, tzinfo=UTC),
        datetime(2020, 4, 1, tzinfo=UTC),
        datetime(2020, 5, 1, tzinfo=UTC),
        datetime(2020, 6, 1, tzinfo=UTC),
    )

    last_updated_dates = (
        datetime(2022, 7, 3, tzinfo=UTC),
        datetime(2022, 8, 3, tzinfo=UTC),
        datetime(2022, 9, 3, tzinfo=UTC),
        datetime(2022, 10, 3, tzinfo=UTC),
        datetime(2022, 11, 3, tzinfo=UTC),
        datetime(2022, 12, 3, tzinfo=UTC),
    )

    estimated_resolution_dates = (
        datetime(2021, 9, 22, tzinfo=UTC),
        datetime(2021, 8, 22, tzinfo=UTC),
        datetime(2021, 7, 22, tzinfo=UTC),
        datetime(2021, 6, 22, tzinfo=UTC),
    )

    impacts = (7, 11, 19)

    def setUp(self):
        super().setUp()
        self.url = reverse("list-barriers")

    def make_barrier(self, **kwargs):
        return BarrierFactory(**kwargs)

    def make_reported_on_barriers(self) -> QuerySet:
        for _ in self.reported_on_dates:
            self.make_barrier()
        for barrier, reported_on_date in zip(
            Barrier.objects.all(), self.reported_on_dates
        ):
            Barrier.objects.filter(pk=barrier.pk).update(reported_on=reported_on_date)
        return Barrier.objects.order_by(settings.BARRIER_LIST_DEFAULT_SORT)

    def make_last_updated_barriers(self) -> QuerySet:
        barriers = self.make_reported_on_barriers()
        for index, date in enumerate(self.last_updated_dates):
            Barrier.objects.filter(pk=barriers[index].pk).update(modified_on=date)
        return Barrier.objects.order_by("modified_on")

    def make_estimated_resolution_date_barriers(self) -> (QuerySet, QuerySet):
        barriers = self.make_reported_on_barriers()
        estimated_resolution_date_barrier_ids = []
        for index, date in enumerate(self.estimated_resolution_dates[0:4]):
            barrier_pk = barriers[index].pk
            estimated_resolution_date_barrier_ids.append(barrier_pk)
            Barrier.objects.filter(pk=barrier_pk).update(estimated_resolution_date=date)
        no_estimated_resolution_date_barriers = Barrier.objects.exclude(
            pk__in=estimated_resolution_date_barrier_ids
        )
        no_estimated_resolution_date_barriers.update(estimated_resolution_date=None)
        estimated_resolution_date_barriers = Barrier.objects.filter(
            estimated_resolution_date__isnull=False
        )
        return estimated_resolution_date_barriers, no_estimated_resolution_date_barriers

    def make_resolved_barriers(self) -> (QuerySet, QuerySet):
        barriers, _ = self.make_estimated_resolution_date_barriers()
        resolved_barrier_ids = [
            barrier.pk
            for barrier in barriers.order_by("estimated_resolution_date")[0:2]
        ]
        Barrier.objects.update(status=BarrierStatus.UNKNOWN)
        Barrier.objects.filter(pk__in=resolved_barrier_ids).update(
            status=BarrierStatus.RESOLVED_IN_FULL
        )
        resolved_barriers = Barrier.objects.filter(
            status=BarrierStatus.RESOLVED_IN_FULL
        )
        unresolved_barriers = Barrier.objects.all().difference(resolved_barriers)
        return resolved_barriers, unresolved_barriers

    def make_economic_impact_assessment_aka_valuation_assessment_barriers(
        self,
    ) -> (QuerySet, QuerySet):
        barriers = self.make_reported_on_barriers()
        for impact, barrier in zip(self.impacts, barriers):
            EconomicImpactAssessmentFactory(
                barrier=barrier,
                impact=impact,
                economic_assessment=EconomicAssessmentFactory(barrier=barrier),
                archived=False,
            )
        barriers_with_value = Barrier.objects.filter(
            valuation_assessments__archived=False, valuation_assessments__isnull=False
        )
        barriers_without_value = Barrier.objects.filter(
            valuation_assessments__isnull=True
        )
        return barriers_with_value, barriers_without_value

    def test_list_barriers_order_by_default_should_be_reported_on_descending(self):
        barriers = self.make_reported_on_barriers().order_by("-reported_on")

        url = f'{reverse("list-barriers")}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_reported_on_descending(self):
        barriers = self.make_reported_on_barriers().order_by("-reported_on")

        url = f'{reverse("list-barriers")}?ordering=-reported'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_reported_on_ascending(self):
        barriers = self.make_reported_on_barriers().order_by("reported_on")

        url = f'{reverse("list-barriers")}?ordering=reported'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_last_updated_descending(self):
        barriers = self.make_last_updated_barriers().order_by("-modified_on")

        url = f'{reverse("list-barriers")}?ordering=-updated'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_last_updated_ascending(self):
        barriers = self.make_last_updated_barriers().order_by("modified_on")

        url = f'{reverse("list-barriers")}?ordering=updated'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_estimated_resolution_descending(self):
        (
            resolution_date_barriers,
            no_resolution_date_barriers,
        ) = self.make_estimated_resolution_date_barriers()
        resolution_date_barriers = resolution_date_barriers.order_by(
            "-estimated_resolution_date"
        )
        no_resolution_date_barriers = no_resolution_date_barriers.order_by(
            "-reported_on"
        )

        url = f'{reverse("list-barriers")}?ordering=-resolution'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [
            str(b.id)
            for b in chain(resolution_date_barriers, no_resolution_date_barriers)
        ]
        assert db_list == response_list

    def test_list_barriers_order_by_estimated_resolution_ascending(self):
        (
            resolution_date_barriers,
            no_resolution_date_barriers,
        ) = self.make_estimated_resolution_date_barriers()
        resolution_date_barriers = resolution_date_barriers.order_by(
            "estimated_resolution_date"
        )
        no_resolution_date_barriers = no_resolution_date_barriers.order_by(
            "-reported_on"
        )

        url = f'{reverse("list-barriers")}?ordering=resolution'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [
            str(b.id)
            for b in chain(resolution_date_barriers, no_resolution_date_barriers)
        ]
        assert db_list == response_list

    def test_list_barriers_order_by_resolved_descending(self):
        resolved_barriers, unresolved_barriers = self.make_resolved_barriers()
        resolved_barriers = resolved_barriers.order_by("-estimated_resolution_date")
        unresolved_barriers = unresolved_barriers.order_by("-reported_on")

        url = f'{reverse("list-barriers")}?ordering=-resolved'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        resolved_barrier_list = [str(b.id) for b in resolved_barriers]
        unresolved_barrier_list = [str(b.id) for b in unresolved_barriers]
        db_list = resolved_barrier_list + unresolved_barrier_list
        assert db_list == response_list

    def test_list_barriers_order_by_resolved_ascending(self):
        resolved_barriers, unresolved_barriers = self.make_resolved_barriers()
        resolved_barriers = resolved_barriers.order_by("estimated_resolution_date")
        unresolved_barriers = unresolved_barriers.order_by("-reported_on")

        url = f'{reverse("list-barriers")}?ordering=resolved'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        resolved_barrier_list = [str(b.id) for b in resolved_barriers]
        unresolved_barrier_list = [str(b.id) for b in unresolved_barriers]
        db_list = resolved_barrier_list + unresolved_barrier_list
        assert db_list == response_list

    def test_list_barriers_order_by_value_descending(self):
        (
            barriers_with_value,
            barriers_without_value,
        ) = self.make_economic_impact_assessment_aka_valuation_assessment_barriers()
        barriers_with_value = barriers_with_value.order_by(
            "-valuation_assessments__impact"
        )
        barriers_without_value = barriers_without_value.order_by("-reported_on")

        url = f'{reverse("list-barriers")}?ordering=-value'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        valued_barrier_list = [str(b.id) for b in barriers_with_value]
        unvalued_barrier_list = [str(b.id) for b in barriers_without_value]
        db_list = valued_barrier_list + unvalued_barrier_list
        assert db_list == response_list

    def test_list_barriers_order_by_value_ascending(self):
        (
            barriers_with_value,
            barriers_without_value,
        ) = self.make_economic_impact_assessment_aka_valuation_assessment_barriers()
        barriers_with_value = barriers_with_value.order_by(
            "valuation_assessments__impact"
        )
        barriers_without_value = barriers_without_value.order_by("-reported_on")

        url = f'{reverse("list-barriers")}?ordering=value'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        valued_barrier_list = [str(b.id) for b in barriers_with_value]
        unvalued_barrier_list = [str(b.id) for b in barriers_without_value]
        db_list = valued_barrier_list + unvalued_barrier_list
        assert db_list == response_list

    def test_list_barriers_with_archived_valuation_assessment_order_by_value_descending(
        self,
    ):
        (
            barriers_with_value,
            barriers_without_value,
        ) = self.make_economic_impact_assessment_aka_valuation_assessment_barriers()
        barriers_with_value = barriers_with_value.order_by(
            "-valuation_assessments__impact"
        )
        barriers_without_value = barriers_without_value.order_by("-reported_on")

        # Give one barrier two assessments, one archived,
        # to ensure only the unarchived one is used for ordering
        barrier_with_archived_assessment = barriers_with_value.first()
        assessment_to_archive: EconomicImpactAssessment = (
            barrier_with_archived_assessment.valuation_assessments.first()
        )
        assessment_to_archive.archive(self.user, "Test archived barrier")
        EconomicImpactAssessmentFactory(
            barrier=barrier_with_archived_assessment,
            impact=min(self.impacts) - 1,
            economic_assessment=assessment_to_archive.economic_assessment,
            archived=False,
        )
        url = f'{reverse("list-barriers")}?ordering=-value'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        # assert len(response_list) == barriers_with_value.count() + barriers_without_value.count()
        valued_barrier_list = [str(b.id) for b in barriers_with_value]
        unvalued_barrier_list = [str(b.id) for b in barriers_without_value]
        db_list = valued_barrier_list + unvalued_barrier_list
        assert db_list == response_list

    def test_list_barriers_with_archived_valuation_assessment_order_by_value_ascending(
        self,
    ):
        (
            barriers_with_value,
            barriers_without_value,
        ) = self.make_economic_impact_assessment_aka_valuation_assessment_barriers()
        barriers_with_value = barriers_with_value.order_by(
            "valuation_assessments__impact"
        )
        barriers_without_value = barriers_without_value.order_by("-reported_on")

        # Give one barrier two assessments, one archived,
        # to ensure only the unarchived one is used for ordering
        barrier_with_archived_assessment = barriers_with_value.last()
        assessment_to_archive: EconomicImpactAssessment = (
            barrier_with_archived_assessment.valuation_assessments.first()
        )
        assessment_to_archive.archive(self.user, "Test archived barrier")
        EconomicImpactAssessmentFactory(
            barrier=barrier_with_archived_assessment,
            impact=max(self.impacts) + 1,
            economic_assessment=assessment_to_archive.economic_assessment,
            archived=False,
        )

        url = f'{reverse("list-barriers")}?ordering=value'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        # assert len(response_list) == barriers_with_value.count() + barriers_without_value.count()
        valued_barrier_list = [str(b.id) for b in barriers_with_value]
        unvalued_barrier_list = [str(b.id) for b in barriers_without_value]
        db_list = valued_barrier_list + unvalued_barrier_list
        assert db_list == response_list
