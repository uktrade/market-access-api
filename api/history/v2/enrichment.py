"""
Enrichments to historical data as done by legacy.
"""
from typing import Dict, List, Optional

from api.metadata.constants import (
    PRIORITY_LEVELS,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_CATEGORIES,
)
from api.metadata.utils import get_location_text, get_sector


def get_matching_history_item(
    history_item: Dict, history: List[Dict]
) -> Optional[Dict]:
    """Given a history_item, find the corresponding history item from another history table w.r.t. time"""
    primary_date = history_item["date"]
    for item in reversed(history):
        if item["date"] <= primary_date:
            return item


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
            return sector["name"]

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


def enrich_top_priority_status(
    barrier_history: List[Dict], top_priority_summary_history: List[Dict]
):
    def enrich(value, summary_text: str):
        status = TOP_PRIORITY_BARRIER_STATUS[value["top_priority_status"]]
        if (
            value["top_priority_status"] == "APPROVED"
            or value["top_priority_status"] == "APPROVAL_PENDING"
            or value["top_priority_status"] == "REMOVAL_PENDING"
            or value["top_priority_status"] == "RESOLVED"
        ):

            # It's an accepted Top Priority Request, or pending review
            top_priority_reason = summary_text
        else:
            # The top_priority_status is NONE
            if value["top_priority_rejection_summary"]:
                # It's a rejected Top Priority Request
                status = "Rejected"
                top_priority_reason = value["top_priority_rejection_summary"] or ""
            else:
                # The barrier has had its top-priority status removed
                status = "Removed"
                top_priority_reason = summary_text

        return {"value": status, "reason": top_priority_reason}

    previous = None
    for item in barrier_history:
        if item["field"] != "top_priority_status":
            continue

        matching_item = get_matching_history_item(item, top_priority_summary_history)
        if (
            matching_item
            and previous
            and previous["new_value"] == matching_item["new_value"]
        ):
            old_matching_value = matching_item["new_value"]
        else:
            old_matching_value = (
                (matching_item["old_value"] or "") if matching_item else ""
            )

        item["model"] = "barrier"  # Backwards compat FE
        item["old_value"] = enrich(item["old_value"], old_matching_value)
        item["new_value"] = enrich(
            item["new_value"],
            (matching_item["new_value"] or "") if matching_item else "",
        )
        previous = matching_item


def enrich_priority(history: List[Dict]):
    def enrich(value):
        if value and value.get("priority") is not None:
            value["priority"] = str(value["priority"])
        return value

    for item in history:
        if item["field"] != "priority":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])
