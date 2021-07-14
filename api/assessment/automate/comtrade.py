from decimal import Decimal
from itertools import chain
from typing import Dict, List, Tuple

from django.db import connections
from psycopg2 import extras, sql
import requests

from .exceptions import CountryNotFound, ExchangeRateNotFound
from .exchange_rates import exchange_rates


class ComtradeClient:
    """
    Client for the Comtrade API

    References:
    https://comtrade.un.org/data/doc/api/#DataRequests
    https://github.com/ropensci/comtradr/blob/c61eb011d604eae1b6d11e0468c6588cd7154b4b/R/ct_search.R

    Update from ticket MAR-1102:
    This data has been moved into our own databse. The UNs' API has not been brought in
    So the old API calls here have been move over to a series of DB calls
    """

    partner_areas_url = "https://comtrade.un.org/Data/cache/partnerAreas.json"
    reporter_areas_url = "https://comtrade.un.org/Data/cache/reporterAreas.json"
    field_mapping = {
        "period": "yr",
        "trade_flow": "rgDesc",
        "report": "rtTitle",
        "partner": "ptTitle",
        "commodity_code": "cmdCode",
        "commodity": "cmdDescE",
        "trade_value_usd": "TradeValue",
    }

    def __init__(self, cache=None):
        self.cache = cache

        data: dict = requests.get(self.partner_areas_url).json()
        self.partner_areas: Dict[str, str] = {
            result["text"]: result["id"] for result in data["results"]
        }

        data: dict = requests.get(self.partner_areas_url).json()
        self.reporter_areas: Dict[str, str] = {
            result["text"]: result["id"] for result in data["results"]
        }

    def get(
        self,
        years: List[str] = [],
        trade_direction: List[str] = [],
        commodity_codes: List[str] = [],
        partners: List[str] = [],
        reporters: List[str] = [],
        tidy=False,
    ):
        period: Tuple[int] = self.get_date_params(years)
        trade_flow_code: Tuple[int] = self.get_trade_direction_params(trade_direction)
        if isinstance(partners, str):
            partners = [partners]
        partner_code: Tuple[int] = self.get_partners_params(partners)
        if isinstance(reporters, str):
            reporters = [reporters]
        reporter_code: Tuple[int] = self.get_reporters_params(reporters)

        query: sql.SQL = sql.SQL(
            "SELECT *, 'TOTAL' as commodity_code FROM comtrade__goods WHERE "
            "period IN ? AND trade_flow_code IN ? partner_code IN ? AND reporter_code IN ?"
        )
        with connections["comtrade"].cursor() as cur:
            cur.execute(query, [period, trade_flow_code, partner_code, reporter_code])
            data = cur.fetchall()

        if not tidy:
            for row in data:
                exchange_rate = exchange_rates.get(str(row["year"]))
                if exchange_rate is None:
                    raise ExchangeRateNotFound(
                        f"Exchange rate not found for year: {row['year']}"
                    )
                row["trade_value_gbp"] = Decimal(row["trade_value_usd"]) / exchange_rate
        else:
            data = self.tidytrade(data)

        return data

    def get_date_params(self, years: List[str]) -> Tuple[int]:
        return tuple([int(year[:4]) for year in years])

    def get_trade_direction_params(self, trade_direction: List[str]) -> Tuple[int]:
        lookup = {
            "all": [1, 2, 3, 4],
            "imports": [1],
            "exports": [2],
            "re_exports": [3],
            "re_imports": [4],
        }
        mapped_values: List[int] = [lookup.get(td) for td in trade_direction]
        return tuple(set(chain(*mapped_values)))  # Flatten, dedupe, cast

    def get_commodity_codes_params(self, commodity_codes: List[str]):
        return {"cc": ",".join(sorted(commodity_codes))}

    def get_partners_params(self, partners: List[str]) -> Tuple[int]:
        try:
            partner_ids: Tuple[int] = tuple(
                [int(self.partner_areas[partner]) for partner in partners]
            )
        except KeyError as e:
            raise CountryNotFound(f"Country not found in Comtrade API: {e}")

        return partner_ids

    def get_reporters_params(self, reporters: List[str]) -> Tuple[int]:

        try:
            reporter_ids = tuple(
                [int(self.reporter_areas[reporter]) for reporter in reporters]
            )
        except KeyError as e:
            raise CountryNotFound(f"Country not found in Comtrade API: {e}")

        return reporter_ids

    def get_valid_years(
        self, target_year: str, country1: str, country2: str
    ) -> List[str]:
        valid_years: List[str] = []

        for year in range(int(target_year), 2000, -1):
            data: List[Dict[str, str]] = self.get(
                years=[str(year)],
                trade_direction=("imports", "exports"),
                commodity_codes="TOTAL",
                reporters=(country1, country2),
                partners="World",
            )
            years: List[str] = [item["yr"] for item in data]

            if len(years) == 4 and all(y == year for y in years):
                valid_years.append(year)

            if len(valid_years) == 3:
                return valid_years

        return valid_years

    def tidytrade(self, rows: Dict[str, str]) -> List[Dict[str, str]]:
        output: List[Dict[str, str]] = []
        for row in rows:
            new_row: Dict[str, str] = {
                value: row.get(key) for key, value in self.field_mapping.items()
            }
            output.append(new_row)
        return output
