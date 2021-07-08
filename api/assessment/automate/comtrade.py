import json
from decimal import Decimal
from typing import List, Dict

from django.conf import settings
from psycopg2 import sql, extras
import psycopg2
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
        self.pg_conn = psycopg2.connect(
            host=settings.COMTRADE_DB_HOST,
            database=settings.COMTRADE_DB_NAME,
            user=settings.COMTRADE_DB_USER,
            password=settings.COMTRADE_DB_PWORD,
            port=settings.COMTRADE_DB_PORT,
            options="-c search_path=un",  # data in un schema not public schema
        )
        self.cache = cache

        data = requests.get(self.partner_areas_url).json()
        self.reporter_areas: Dict[str, str] = {
            result["text"]: result["id"] for result in data["results"]
        }

        data = requests.get(self.partner_areas_url).json()
        self.reporter_areas: Dict[str, str] = {
            result["text"]: result["id"] for result in data["results"]
        }

    def get(
        self,
        years=None,
        trade_direction=None,
        commodity_codes=None,
        partners=None,
        reporters=None,
        tidy=False,
    ):
        query = sql.SQL(
            "SELECT * FROM comtrade__goods WHERE period IN ? AND trade_flow_control IN ? partner_code IN ? AND reporter_code IN ?"
        )
        with self.pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            pass
        if isinstance(commodity_codes, str):
            commodity_codes = (commodity_codes.lower(),)

        data = self.fetch(url)
        dataset = data["dataset"]

        if tidy:
            return self.tidytrade(dataset)
        return dataset

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

    def get_date_params(self, years):
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

    def get_valid_years(self, target_year, country1, country2):
        valid_years = []

        for year in range(target_year, 2000, -1):
            data = self.get(
                years=[year],
                trade_direction=("imports", "exports"),
                commodity_codes="TOTAL",
                reporters=(country1, country2),
                partners="World",
            )
            years = [item["yr"] for item in data]

            if len(years) == 4 and all(y == year for y in years):
                valid_years.append(year)

            if len(valid_years) == 3:
                return valid_years

        return valid_years
