from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user

from api.metadata.models import BarrierType


class TestBarrierTypes(APITestMixin):
    def test_barrier_types_count(self):
        barrier_types_count = BarrierType.objects.count()
        assert barrier_types_count == 32

    def test_barrier_types_goods_count(self):
        barrier_types_count = BarrierType.goods.count()
        assert barrier_types_count == 25

    def test_barrier_types_services_count(self):
        barrier_types_count = BarrierType.services.count()
        assert barrier_types_count == 22
