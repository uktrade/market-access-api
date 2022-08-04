from datetime import datetime

from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin
from api.metadata.constants import SEARCH_ORDERING_CHOICES, BarrierStatus
from tests.barriers.factories import BarrierFactory


class TestListBarriersOrdering(APITestMixin, APITestCase):
    bahamas = "a25f66a0-5d95-e211-a939-e4115bead28a"
    bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
    spain = "86756b9a-5d95-e211-a939-e4115bead28a"

    countries = (bahamas, bhutan, spain)

    reported_on_dates = (
        datetime(2020, 1, 3, tzinfo=UTC),
        datetime(2020, 2, 3, tzinfo=UTC),
        datetime(2020, 3, 3, tzinfo=UTC),
        datetime(2020, 4, 3, tzinfo=UTC),
        datetime(2020, 5, 3, tzinfo=UTC),
        datetime(2020, 6, 3, tzinfo=UTC),
    )

    estimated_resolution_dates = (
        datetime(2021, 6, 3, tzinfo=UTC),
        datetime(2021, 1, 3, tzinfo=UTC),
        datetime(2021, 5, 3, tzinfo=UTC),
        datetime(2021, 3, 3, tzinfo=UTC),
        datetime(2021, 4, 3, tzinfo=UTC),
        datetime(2021, 2, 3, tzinfo=UTC),
    )

    last_updated_dates = (
        datetime(2022, 5, 3, tzinfo=UTC),
        datetime(2022, 4, 3, tzinfo=UTC),
        datetime(2022, 6, 3, tzinfo=UTC),
        datetime(2022, 8, 3, tzinfo=UTC),
        datetime(2022, 7, 3, tzinfo=UTC),
        datetime(2022, 9, 3, tzinfo=UTC),
    )

    def setUp(self):
        super().setUp()
        self.url = reverse("list-barriers")

    def make_barrier(self, **kwargs):
        return BarrierFactory(**kwargs)

    def make_reported_on_barriers(self, limit=None):
        if limit is None:
            limit = len(self.reported_on_dates)
        [
            self.make_barrier(reported_on=reported_on_date)
            for reported_on_date in self.reported_on_dates[0:limit]
        ]
        return Barrier.objects.order_by("reported_on")

    def make_last_updated_barriers(self, limit=None):
        if limit is None:
            limit = len(self.last_updated_dates)
        barriers = self.make_reported_on_barriers(limit=limit)
        for index, date in enumerate(self.last_updated_dates[0:limit]):
            Barrier.objects.filter(pk=barriers[index].pk).update(modified_on=date)
        return Barrier.objects.order_by("modified_on")

    def make_estimated_resolution_date_barriers(self, limit=None):
        if limit is None:
            limit = len(self.estimated_resolution_dates)
        [
            self.make_barrier(
                reported_on=reported_on_date, estimated_resolution_date=resolution_date
            )
            for reported_on_date, resolution_date in zip(
                self.reported_on_dates[0:limit],
                self.estimated_resolution_dates[0:limit],
            )
        ]
        return Barrier.objects.order_by("estimated_resolution_date")

    def make_resolved_barriers(self, limit=None):
        barriers = self.make_estimated_resolution_date_barriers()
        count = barriers.count()
        resolved_barrier_ids = [
            barrier.pk for barrier in barriers[0 : barriers.count() : 2]
        ]
        barriers.filter(pk__in=resolved_barrier_ids).update(
            status=BarrierStatus.RESOLVED_IN_FULL
        )
        barriers.exclude(pk__in=resolved_barrier_ids).update(
            status=BarrierStatus.UNKNOWN
        )
        resolved_barriers = Barrier.objects.filter(
            status=BarrierStatus.RESOLVED_IN_FULL
        )
        unresolved_barriers = Barrier.objects.all().difference(resolved_barriers)
        return resolved_barriers.order_by(
            "estimated_resolution_date"
        ), unresolved_barriers.order_by("-reported_on")

    def test_list_barriers_order_by_reported_on_descending(self):
        third, second, first = self.make_reported_on_barriers(limit=3)

        order_by = SEARCH_ORDERING_CHOICES["Date reported (newest)"]["ordering"]
        url = f'{reverse("list-barriers")}?ordering={order_by}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        barriers = [first, second, third]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_reported_on_ascending(self):
        first, second, third = self.make_reported_on_barriers(limit=3)

        order_by = SEARCH_ORDERING_CHOICES["Date reported (oldest)"]["ordering"]
        url = f'{reverse("list-barriers")}?ordering={order_by}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        barriers = [first, second, third]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_last_updated_descending(self):
        third, second, first = self.make_last_updated_barriers(limit=3)

        order_by = SEARCH_ORDERING_CHOICES["Last updated (most recent)"]["ordering"]
        url = f'{reverse("list-barriers")}?ordering={order_by}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        barriers = [first, second, third]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_last_updated_ascending(self):
        first, second, third = self.make_last_updated_barriers(limit=3)

        order_by = SEARCH_ORDERING_CHOICES["Last updated (least recent)"]["ordering"]
        url = f'{reverse("list-barriers")}?ordering={order_by}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        barriers = [first, second, third]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_estimated_resolution_descending(self):
        third, second, first = self.make_estimated_resolution_date_barriers(limit=3)

        order_by = SEARCH_ORDERING_CHOICES["Estimated resolution date (most recent)"][
            "ordering"
        ]
        url = f'{reverse("list-barriers")}?ordering={order_by}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        barriers = [first, second, third]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_estimated_resolution_ascending(self):
        first, second, third = self.make_estimated_resolution_date_barriers(limit=3)

        order_by = SEARCH_ORDERING_CHOICES["Estimated resolution date (least recent)"][
            "ordering"
        ]
        url = f'{reverse("list-barriers")}?ordering={order_by}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        barriers = [first, second, third]
        db_list = [str(b.id) for b in barriers]
        assert db_list == response_list

    def test_list_barriers_order_by_resolved_descending(self):
        resolved_barriers, unresolved_barriers = self.make_resolved_barriers()
        resolved_barriers = resolved_barriers.order_by("-estimated_resolution_date")

        ordering_configuration = SEARCH_ORDERING_CHOICES["Date resolved (most recent)"]
        order_by = ordering_configuration["ordering"]
        ordering_filter = ordering_configuration["ordering-filter"]
        url = f'{reverse("list-barriers")}?ordering={order_by}&ordering-filter={ordering_filter}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        resolved_barrier_list = [str(b.id) for b in resolved_barriers]
        unresolved_barrier_list = [str(b.id) for b in unresolved_barriers]
        db_list = resolved_barrier_list + unresolved_barrier_list
        assert db_list == response_list

    def test_list_barriers_order_by_resolved_ascending(self):
        resolved_barriers, unresolved_barriers = self.make_resolved_barriers()

        ordering_configuration = SEARCH_ORDERING_CHOICES["Date resolved (least recent)"]
        order_by = ordering_configuration["ordering"]
        ordering_filter = ordering_configuration["ordering-filter"]
        url = f'{reverse("list-barriers")}?ordering={order_by}&ordering-filter={ordering_filter}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_list = [b["id"] for b in response.data["results"]]
        resolved_barrier_list = [str(b.id) for b in resolved_barriers]
        unresolved_barrier_list = [str(b.id) for b in unresolved_barriers]
        db_list = resolved_barrier_list + unresolved_barrier_list
        assert db_list == response_list
