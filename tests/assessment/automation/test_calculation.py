import os
from typing import Dict

import pytest
import simplejson as json
from jsondiff import diff
from mock import patch

from api.assessment.automate.calculator import AssessmentCalculator
from api.assessment.automate.comtrade import ComtradeClient
from api.core.test_utils import APITestMixin
from tests.assessment.automation.utils import patched_comtrade_fetch
from tests.barriers.factories import BarrierFactory, CommodityFactory

pytestmark = [pytest.mark.django_db]


class TestAssessmentUtils(APITestMixin):
    def matches_snapshot(self, test_name: str, test_data: Dict):
        dirname = os.path.dirname(__file__)
        snapshot_filename = os.path.join(dirname, "snapshots", f"{test_name}.json")
        try:
            with open(snapshot_filename, "r") as snapshot_file:
                snapshot_data = json.load(snapshot_file)
        except Exception:
            with open(snapshot_filename, "w") as snapshot_file:
                snapshot_data = json.dump(test_data, snapshot_file, use_decimal=True)
            snapshot_data = test_data
        return bool(
            diff(
                json.dumps(test_data, sort_keys=True, use_decimal=True),
                json.dumps(snapshot_data, sort_keys=True, use_decimal=True),
                load=True,
                dump=True,
            )
        )

    @patch.object(ComtradeClient, "fetch", new=patched_comtrade_fetch)
    def test_assessment_calculator(self):
        country_commodity_pairs = [
            {
                "country": "5961b8be-5d95-e211-a939-e4115bead28a",  # Russia,
                "commodities": ["010410", "010410"],
            },
            {
                "country": "a15f66a0-5d95-e211-a939-e4115bead28a",  # Azerbaijan,
                "commodities": ["7304", "7306", "8207", "8459", "8905"],
            },
            {
                "country": "5961b8be-5d95-e211-a939-e4115bead28a",  # Russia,
                "commodities": [
                    "0105",
                    "0207",
                    "040711",
                    "040719",
                ],
            },
            {
                "country": "a45f66a0-5d95-e211-a939-e4115bead28a",  # Bangladesh
                "commodities": ["9301", "930591"],
            },
            {
                "country": "1a0be5c4-5d95-e211-a939-e4115bead28a",  # Saudi Arabia
                "commodities": [
                    "020410",
                    "020421",
                    "020441",
                    "020430",
                ],
            },
        ]

        for country_commodity_pair in country_commodity_pairs:
            country, commodities = country_commodity_pair.values()

            barrier = BarrierFactory(country=country, product="Test product")
            barrier.commodities.set(
                [CommodityFactory(code=code) for code in commodities]
            )

            assessment_calculator = AssessmentCalculator()
            commodity_codes = sorted(
                [c.trimmed_code for c in barrier.commodities.all()]
            )

            result = assessment_calculator.calculate(
                commodity_codes=commodity_codes,
                product=barrier.product,
                country1=barrier.country_name,
            )

            joined_commodity_codes = "_".join(commodities)
            snapshot_name = f"{country}_{joined_commodity_codes}"
            assert self.matches_snapshot(snapshot_name, result)
