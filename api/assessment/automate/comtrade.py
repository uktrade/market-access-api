import json
import psycopg2
import requests

from decimal import Decimal
from psycopg2 import sql
from typing import List

from django.conf import settings

from .exceptions import CountryNotFound, ExchangeRateNotFound
from .exchange_rates import exchange_rates


def make_dict_results(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


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
    _partner_areas = None
    _reporter_areas = None
    IMPORTS_TRADE_FLOW_CODE = 1
    EXPORTS_TRADE_FLOW_CODE = 2

    def __init__(self, cache=None):
        self.cache = cache
        self.db_conn = psycopg2.connect(
            host=settings.COMTRADE_DB_HOST,
            port=settings.COMTRADE_DB_PORT,
            dbname=settings.COMTRADE_DB_NAME,
            user=settings.COMTRADE_DB_USER,
            password=settings.COMTRADE_DB_PWORD,
            options=settings.COMTRADE_DB_OPTIONS,
        )

    def fetch(self, url):
        if self.cache:
            cache_key = f"comtrade-api:{url}"
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

    def get(
        self,
        years,
        partners,
        commodity_codes=None,
        reporters=None,
    ):
        if not commodity_codes:
            commodity_codes = ["TOTAL"]

        conditions = [
            ("commodity_code IN %s", tuple(commodity_codes)),
            ("period IN %s", tuple(years)),
            (
                "trade_flow_code IN %s",
                (self.IMPORTS_TRADE_FLOW_CODE, self.EXPORTS_TRADE_FLOW_CODE),
            ),
        ]
        partner_code = self.get_partners_params(partners)
        if partner_code:
            conditions.append(("partner_code IN %s", partner_code))
        if reporters:
            reporter_code = self.get_reporters_params(reporters)
            if reporter_code:
                conditions.append(("reporter_code IN %s", reporter_code))

        query: sql.SQL = sql.SQL("SELECT * FROM comtrade__goods WHERE {}").format(
            sql.SQL(" AND ").join(sql.SQL(clause) for clause, _ in conditions)
        )
        values = [val for _, val in conditions]
        with self.db_conn.cursor() as cursor:
            cursor.execute(query, values)
            data = make_dict_results(cursor)

        return self.add_gbp_trade_value(data)

    def add_gbp_trade_value(self, rows):
        output = []
        for row in rows:
            new_row = row.copy()
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

    def get_partners_params(self, partners):
        try:
            partner_ids = tuple(
                [int(self.partner_areas[partner]) for partner in partners]
            )
        except KeyError as e:
            raise CountryNotFound(f"Country not found in Comtrade API: {e}")

        return partner_ids

    def get_reporters_params(self, reporters):
        try:
            reporter_ids = tuple(
                [int(self.reporter_areas[reporter]) for reporter in reporters]
            )
        except KeyError as e:
            raise CountryNotFound(f"Country not found in Comtrade API: {e}")

        return reporter_ids

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

    def get_valid_years(self, target_year, country1, country2):
        query = sql.SQL(
            "SELECT year FROM comtrade__goods WHERE "
            "commodity_code = 'TOTAL' AND "
            "trade_flow_code IN {} AND "
            "period = %s AND "
            "partner_code = %s AND "
            "reporter_code IN %s",
        ).format(
            sql.Literal((self.IMPORTS_TRADE_FLOW_CODE, self.EXPORTS_TRADE_FLOW_CODE)),
        )

        valid_years = []
        for year in range(target_year, 2000, -1):
            partner_code = self.partner_areas["World"]
            reporters_codes = (
                self.reporter_areas[country1],
                self.reporter_areas[country2],
            )
            parameters = [
                year,
                partner_code,
                reporters_codes,
            ]

            years = []
            with self.db_conn.cursor() as cursor:
                cursor.execute(query, parameters)
                for row in cursor.fetchall():
                    years.append(row[0])

            if len(years) == 4 and all(y == year for y in years):
                valid_years.append(year)

            if len(valid_years) == 3:
                return valid_years

        return valid_years
