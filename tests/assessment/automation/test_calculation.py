from api.assessment.automate.comtrade import ComtradeClient
from tests.assessment.automation.utils import patched_comtrade_fetch
from mock import patch
from api.assessment.automate.calculator import AssessmentCalculator
from api.assessment.utils import calculate_barrier_economic_assessment
from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse
from django.core.cache import cache
from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory, CommodityFactory

pytestmark = [pytest.mark.django_db]


class TestAssessmentUtils(APITestMixin):
    @pytest.fixture
    def barrier(self):
        barrier = BarrierFactory(
            country="5961b8be-5d95-e211-a939-e4115bead28a"  # Russia
        )
        barrier.commodities.set((CommodityFactory(code="010410"),))
        return barrier

    # @patch.object(ComtradeClient, "fetch", new=patched_comtrade_fetch)
    def test_calculate_barrier_economic_assessment(self, barrier):
        assessment_calculator = AssessmentCalculator()
        commodity_codes = [c.trimmed_code for c in barrier.commodities.all()]

        result = assessment_calculator.calculate(
            commodity_codes=commodity_codes,
            product=barrier.product,
            country1=barrier.country_name,
        )

        assert result == "MOCK_RETURN_VALUE"
