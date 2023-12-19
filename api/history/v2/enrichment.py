"""
Enrichments to historical data as done by legacy.
"""
from datetime import datetime
from typing import Dict, List, Optional

from api.metadata.constants import (
    PRIORITY_LEVELS,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_CATEGORIES,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.metadata.utils import (
    get_country,
    get_location_text,
    get_sector,
    get_trading_bloc,
)

from django.contrib.auth import get_user_model


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


def enrich_sectors(history: List[Dict]):
    for item in history:
        if item["field"] != "sectors":
            continue
        item["old_value"]["sectors"] = [
            str(sector) for sector in item["old_value"]["sectors"]
        ]
        item["new_value"]["sectors"] = [
            str(sector) for sector in item["new_value"]["sectors"]
        ]


def enrich_status(history: List[Dict]):
    for item in history:
        if item["field"] != "status":
            continue
        item["old_value"]["status"] = str(item["old_value"]["status"])
        item["new_value"]["status"] = str(item["new_value"]["status"])


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
        # Same logic as legacy
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

        # Corresponding top_priority_summary history
        matching_item = get_matching_history_item(item, top_priority_summary_history)
        if (
            matching_item
            and previous
            and previous["new_value"] == matching_item["new_value"]
        ):
            # If no change in history
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


def enrich_commodities(history: List[Dict]):
    def enrich(value):
        for commodity in value or []:
            if commodity.get("country"):
                commodity["country"] = get_country(commodity["country"].get("id"))
            elif commodity.get("trading_bloc"):
                commodity["trading_bloc"] = get_trading_bloc(
                    commodity["trading_bloc"].get("code")
                )
        return value

    for item in history:
        if item["field"] != "commodities":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_committee_raised_in(history: List[Dict]):
    def enrich(value):
        if value and value.get("committee_raised_in"):
            committee_raised_in = value["committee_raised_in"]
            committee_raised_in = {
                "id": str(committee_raised_in.get("id")),
                "name": committee_raised_in.get("name"),
            }
            value["committee_raised_in"] = committee_raised_in
        return value

    for item in history:
        if item["field"] != "committee_raised_in":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_committee_notified(history: List[Dict]):
    def enrich(value):
        if value and value.get("committee_notified"):
            committee_notified = value["committee_notified"]
            committee_notified = {
                "id": str(committee_notified.get("id")),
                "name": committee_notified.get("name"),
            }
            value["committee_notified"] = committee_notified
        return value

    for item in history:
        if item["field"] != "committee_notified":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_meeting_minutes(history: List[Dict]):
    def enrich(value):
        if value and value.get("meeting_minutes"):
            meeting_minutes = value["meeting_minutes"]
            meeting_minutes = {
                "id": str(meeting_minutes.get("id")),
                "name": meeting_minutes.get("original_filename"),
            }
            value["meeting_minutes"] = meeting_minutes
        return value

    for item in history:
        if item["field"] != "meeting_minutes":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_wto_notified_status(history: List[Dict]):

    for item in history:
        if item["field"] != "wto_has_been_notified":
            continue

        item["field"] = "wto_notified_status"


def enrich_committee_notification_document(history: List[Dict]):
    def enrich(value):
        if value and value.get("committee_notification_document"):
            committee_notification_document = value["committee_notification_document"]
            committee_notification_document = {
                "id": str(committee_notification_document.get("id")),
                "name": committee_notification_document.get("original_filename"),
            }
            value["committee_notification_document"] = committee_notification_document
        return value

    for item in history:
        if item["field"] != "committee_notification_document":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_note_archived(history: List[Dict]):
    def enrich(value):
        if value and value.get("archived") is not None:
            value["archived"] = {"archived": value["archived"], "text": value["text"]}
        return value

    for item in history:
        if item["field"] != "archived":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_categories(history: List[Dict]):
    def enrich(value):
        if value and value.get("categories_cache"):
            value["categories"] = value.get("categories_cache") or []
        return value

    for item in history:
        if item["field"] != "categories_cache":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_light_touch_reviews(history: List[Dict]):
    def enrich(value):
        if value and value.get("light_touch_reviews_cache"):
            value["light_touch_reviews"] = value.get("light_touch_reviews_cache")
        return value

    for item in history:
        if item["field"] != "light_touch_reviews_cache":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_location(history: List[Dict]):
    def enrich(value):
        if value and value.get("location"):
            value["location"] = get_location_text(
                country_id=value["country"],
                trading_bloc=value["trading_bloc"],
                caused_by_trading_bloc=value["caused_by_trading_bloc"],
            )
        return value

    for item in history:
        if item["field"] != "location":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_sectors(history: List[Dict]):
    def enrich(value):
        if value and value.get("sectors"):
            value["sectors"] = {
                "sectors": [str(sector) for sector in value["sectors"]],
                "all_sectors": value["all_sectors"],
            }
        return value

    for item in history:
        if item["field"] != "sectors":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_public_view_status(history: List[Dict]):
    def enrich(value):
        if value and value.get("public_view_status"):
            barrier_record = value["barrier"].history.as_of(
                value["history_date"] + datetime.timedelta(seconds=1)
            )

            value["public_view_status"] = {
                "id": value["public_view_status"],
                "name": PublicBarrierStatus.choices[value["public_view_status"]],
            }
            value["public_eligibility"] = barrier_record.public_eligibility
            value[
                "public_eligibility_summary"
            ] = barrier_record.public_eligibility_summary
        return value

    for item in history:
        if item["field"] != "public_view_status":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_status(history: List[Dict]):
    def is_resolved(status: str):
        return status == BarrierStatus.RESOLVED_IN_FULL

    def enrich(value):
        if value and value.get("status"):
            value["status"] = {
                "status": str(value["status"]),
                "status_date": value["status_date"],
                "is_resolved": is_resolved(str(value["status"])),
            }
        return value

    for item in history:
        if item["field"] != "status":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_team_member_user(history: List[Dict]):
    def enrich(value, matching_item_dict, is_old):
        key = "old_value" if is_old else "new_value"
        if value and isinstance(value, int):
            user_model = get_user_model()
            user = user_model.objects.filter(id=value).first()
            new_data = {
                "user": {
                    "id": value,
                    "name": f"{user.first_name} {user.last_name}"
                    if user
                    else "Unknown",
                }
            }
            if matching_item_dict["field"] == "role":
                new_data["role"] = matching_item_dict[key]
            return new_data
        return value

    for item in history:
        if item["field"] != "user":
            continue

        # search for the nrole value in history
        matching_item = get_matching_history_item(item, history)
        item["old_value"] = enrich(item["old_value"], matching_item, is_old=True)
        item["new_value"] = enrich(item["new_value"], matching_item, is_old=False)
