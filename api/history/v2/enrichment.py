"""
Enrichments to historical data as done by legacy.
"""
from typing import Dict, List

from api.metadata.constants import PRIORITY_LEVELS, TRADE_CATEGORIES
from api.metadata.utils import get_location_text, get_sector


def enrich_country(history: List[Dict]):
    for item in history:
        if item["field"] != "country":
            continue

        item["field"] = "location"
        item["old_value"] = get_location_text(
            country_id=item["old_value"]["country"],
            trading_bloc=item["old_value"]["trading_bloc"],
            caused_by_trading_bloc=item["old_value"]["caused_by_trading_bloc"],
            admin_area_ids=item["old_value"]["admin_areas"],
        )
        item["new_value"] = get_location_text(
            country_id=item["new_value"]["country"],
            trading_bloc=item["new_value"]["trading_bloc"],
            caused_by_trading_bloc=item["new_value"]["caused_by_trading_bloc"],
            admin_area_ids=item["new_value"]["admin_areas"],
        )


def enrich_trade_category(history: List[Dict]):
    def enrich(value):
        if not value:
            return
        return {"id": value, "name": TRADE_CATEGORIES[value]}

    for item in history:
        if item["field"] != "trade_category":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_main_sector(history: List[Dict]):
    def enrich(value):
        sector = get_sector(value)
        if sector:
            return sector['name']

    for item in history:
        if item["field"] != "main_sector":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_priority_level(history: List[Dict]):
    def enrich(value):
        if not value:
            return
        return PRIORITY_LEVELS[value]

    for item in history:
        if item["field"] != "priority_level":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])
