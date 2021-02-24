import json
from decimal import Decimal
from typing import List

import requests

from .exceptions import CountryNotFound, ExchangeRateNotFound
from .exchange_rates import exchange_rates


class ComtradeClient:
    """
    Client for the Comtrade API

    References:
    https://comtrade.un.org/data/doc/api/#DataRequests
    https://github.com/ropensci/comtradr/blob/c61eb011d604eae1b6d11e0468c6588cd7154b4b/R/ct_search.R
    """

    base_url = "https://comtrade.un.org/api/get"
    partner_areas_url = "https://comtrade.un.org/Data/cache/partnerAreas.json"
    reporter_areas_url = "https://comtrade.un.org/Data/cache/reporterAreas.json"
    field_mapping = {
        "yr": "year",
        "rgDesc": "trade_flow",
        "rtTitle": "reporter",
        "ptTitle": "partner",
        "cmdCode": "commodity_code",
        "cmdDescE": "commodity",
        "TradeValue": "trade_value_usd",
    }
    _partner_areas = None
    _reporter_areas = None

    def __init__(self, cache=None):
        self.cache = cache

    def get(
        self,
        start_year=None,
        end_year=None,
        trade_direction=None,
        commodity_codes=None,
        partners=None,
        reporters=None,
        tidy=False,
    ):
        if isinstance(commodity_codes, str):
            commodity_codes = (commodity_codes.lower(),)

        # Restrict to 5 commodity codes per API call
        if len(commodity_codes) > 5:
            return self.get(
                start_year=start_year,
                end_year=end_year,
                trade_direction=trade_direction,
                commodity_codes=commodity_codes[:5],
                partners=partners,
                reporters=reporters,
                tidy=tidy,
            ) + self.get(
                start_year=start_year,
                end_year=end_year,
                trade_direction=trade_direction,
                commodity_codes=commodity_codes[5:],
                partners=partners,
                reporters=reporters,
                tidy=tidy,
            )

        params = self.get_params(
            start_year, end_year, trade_direction, commodity_codes, partners, reporters
        )

        querystring = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.base_url}?{querystring}"
        data = self.fetch(url)
        dataset = data["dataset"]

        if tidy:
            return self.tidytrade(dataset)
        return dataset

    def fetch(self, url):
        if self.cache:
            cache_key = f"comtrade:{url}"
            data = self.cache.get(cache_key)
            if data:
                return data

        response = requests.get(url)
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            # try to handle - Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
            data = json.loads(response.content.decode("utf-8-sig"))

        if self.cache:
            self.cache.set(cache_key, data, 7200)
        return data

    def get_params(
        self,
        start_year=None,
        end_year=None,
        trade_direction=None,
        commodity_codes=None,
        partners=None,
        reporters=None,
    ):
        params = {"fmt": "json"}
        if start_year and end_year:
            params.update(self.get_date_params(start_year, end_year))
        if trade_direction:
            params.update(self.get_trade_direction_params(trade_direction))
        if commodity_codes:
            params.update(self.get_commodity_codes_params(commodity_codes))
        if partners:
            params.update(self.get_partners_params(partners))
        if reporters:
            params.update(self.get_reporters_params(reporters))
        return params

    def tidytrade(self, rows):
        output = []
        for row in rows:
            new_row = {value: row.get(key) for key, value in self.field_mapping.items()}
            exchange_rate = exchange_rates.get(str(new_row["year"]))
            if exchange_rate is None:
                raise ExchangeRateNotFound(
                    f"Exchange rate not found for year: {new_row['year']}"
                )
            new_row["trade_value_gbp"] = (
                Decimal(new_row["trade_value_usd"]) / exchange_rate
            )
            output.append(new_row)
        return output

    def get_date_params(self, start_year, end_year):
        years = range(start_year, end_year + 1)
        return {"ps": ",".join([str(year) for year in years])}

    def get_trade_direction_params(self, trade_direction):
        lookup = {
            "all": "all",
            "imports": "1",
            "exports": "2",
            "re_exports": "3",
            "re_imports": "4",
        }
        return {"rg": ",".join([lookup.get(td) for td in trade_direction])}

    def get_commodity_codes_params(self, commodity_codes: List[str]):
        return {"cc": ",".join(sorted(commodity_codes))}

    def get_partners_params(self, partners):
        if isinstance(partners, str):
            partners = [partners]

        try:
            partner_ids = [self.partner_areas[partner] for partner in partners]
        except KeyError as e:
            raise CountryNotFound(f"Country not found in Comtrade API: {e}")

        return {"p": ",".join(partner_ids)}

    def get_reporters_params(self, reporters):
        if isinstance(reporters, str):
            reporters = [reporters]

        try:
            reporter_ids = [self.reporter_areas[reporter] for reporter in reporters]
        except KeyError as e:
            raise CountryNotFound(f"Country not found in Comtrade API: {e}")

        return {"r": ",".join(reporter_ids)}

    @property
    def partner_areas(self):
        if self._partner_areas is None:
            data = self.fetch(self.partner_areas_url)
            self._partner_areas = {
                result["text"]: result["id"] for result in data["results"]
            }
        return self._partner_areas

    @property
    def reporter_areas(self):
        if self._reporter_areas is None:
            data = self.fetch(self.reporter_areas_url)
            self._reporter_areas = {
                result["text"]: result["id"] for result in data["results"]
            }
        return self._reporter_areas

    def get_valid_year(self, target_year, country1, country2):
        for year in range(target_year, 2000, -1):
            data = self.get(
                start_year=year,
                end_year=year,
                trade_direction=("imports", "exports"),
                commodity_codes="TOTAL",
                reporters=(country1, country2),
                partners="World",
            )
            years = [item["yr"] for item in data]

            if len(years) == 4 and all(y == year for y in years):
                return year
