from api.assessment.automate.countries import get_comtrade_country_name
from mock import patch
from api.assessment.automate.calculator import AssessmentCalculator
from api.assessment.utils import calculate_barrier_economic_assessment
from http import HTTPStatus

import pytest
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory, CommodityFactory

pytestmark = [pytest.mark.django_db]


class TestAutomationCountries:
    def test_get_comtrade_country_name(self):
        assert "World" == get_comtrade_country_name("World")
        assert "Russian Federation" == get_comtrade_country_name("Russia")
        assert "Dem. Rep. of the Congo" == get_comtrade_country_name(
            "Congo (Democratic Republic)"
        )
        assert "United Kingdom" == get_comtrade_country_name("United Kingdom")
        assert "Anything not included" == get_comtrade_country_name(
            "Anything not included"
        )
        assert "PreSErvE CaSiNg" == get_comtrade_country_name("PreSErvE CaSiNg")
