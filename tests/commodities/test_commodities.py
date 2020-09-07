from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.core.test_utils import APITestMixin
from tests.barriers.factories import BarrierFactory, CommodityFactory


class CommoditiesTest(APITestMixin, TestCase):
    country_id = "80756b9a-5d95-e211-a939-e4115bead28a"
    trading_bloc_id = "TB00016"

    def setUp(self):
        CommodityFactory(code="2105000000", description="Ice cream")
        CommodityFactory(code="1704903000", description="White chocolate")
        CommodityFactory(code="0810200000", description="Other fruit")
        CommodityFactory(code="0810201000", description="Raspberries")

    def test_commodity_list(self):
        url = reverse("commodity-list")
        response = self.api_client.get(url, {"codes": "2105,1704903000"})

        assert status.HTTP_200_OK == response.status_code
        results_codes = [result["code"] for result in response.data["results"]]
        assert set(results_codes) == set(["2105000000", "1704903000"])

    def test_commodity_detail(self):
        url = reverse("commodity-detail", kwargs={"code": "2105"})
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert response.data["code"] == "2105000000"
        assert response.data["description"] == "Ice cream"

    def test_update_barrier_commodities(self):
        barrier = BarrierFactory()
        url = reverse("get-barrier", kwargs={"pk": barrier.id})
        response = self.api_client.patch(
            url,
            format="json",
            data={
                "commodities": [
                    {"code": "2105000099", "country": self.country_id},
                    {"code": "0810201000", "trading_bloc": self.trading_bloc_id},
                ],
            },
        )

        assert status.HTTP_200_OK == response.status_code

        assert len(response.data["commodities"]) == 2

        commodity_data = response.data["commodities"][0]
        assert commodity_data["code"] == "2105000099"
        assert commodity_data["country"]["id"] == self.country_id
        assert commodity_data["trading_bloc"] is None
        assert commodity_data["commodity"]["code"] == "2105000000"
        assert commodity_data["commodity"]["description"] == "Ice cream"

        commodity_data = response.data["commodities"][1]
        assert commodity_data["code"] == "0810201000"
        assert commodity_data["country"] is None
        assert commodity_data["trading_bloc"]["code"] == self.trading_bloc_id
        assert commodity_data["commodity"]["code"] == "0810200000"
        assert commodity_data["commodity"]["description"] == "Other fruit"
