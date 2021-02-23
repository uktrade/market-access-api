from mock import patch
from api.assessment.automate.calculator import AssessmentCalculator
from api.assessment.utils import calculate_barrier_economic_assessment
from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory, CommodityFactory

pytestmark = [pytest.mark.django_db]


class TestAssessmentUtils(APITestMixin):
    @pytest.fixture
    def barrier(self):
        barrier = BarrierFactory(country="5961b8be-5d95-e211-a939-e4115bead28a")
        barrier.commodities.set((CommodityFactory(code="010410"),))
        return barrier

    @patch.object(AssessmentCalculator, "calculate", return_value="MOCK_RETURN_VALUE")
    def test_calculate_barrier_economic_assessment(self, mock_calculate, barrier):
        result = calculate_barrier_economic_assessment(barrier.id)
        mock_calculate.assert_called_once_with(
            commodity_codes=[commodity.code for commodity in barrier.commodities.all()],
            product=barrier.product,
            country1=barrier.country_name,
        )
        assert result == "MOCK_RETURN_VALUE"
