"""
Enrichments to historical data as done by legacy.
"""

from collections import namedtuple
from datetime import datetime
from typing import Dict, List, Optional

from pytz import UTC

from api.assessment.constants import PRELIMINARY_ASSESSMENT_CHOICES
from api.core.utils import cleansed_username
from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT,
    ECONOMIC_ASSESSMENT_RATING,
    PRIORITY_LEVELS,
    RESOLVABILITY_ASSESSMENT_EFFORT,
    RESOLVABILITY_ASSESSMENT_TIME,
    STRATEGIC_ASSESSMENT_SCALE,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_CATEGORIES,
    PublicBarrierStatus,
)
from api.metadata.utils import (
    get_country,
    get_location_text,
    get_sector,
    get_trading_bloc,
)
from api.wto.models import WTOCommittee


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


def enrich_preliminary_assessment(history: List[Dict]):
    for item in history:
        if item["field"] != "value":
            continue
        if item["old_value"]:
            item["old_value"] = PRELIMINARY_ASSESSMENT_CHOICES[item["old_value"]]
        item["new_value"] = PRELIMINARY_ASSESSMENT_CHOICES[item["new_value"]]


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
        if value:
            committee = WTOCommittee.objects.get(id=value)
            return {
                "id": str(committee.id),
                "name": committee.name,
            }
        return value

    for item in history:
        if item["field"] != "committee_raised_in":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_rating(history: List[Dict]):
    def enrich(value):
        if value:
            return {"id": value, "name": ECONOMIC_ASSESSMENT_RATING[value]}

    for item in history:
        if item["field"] != "rating":
            continue
        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_committee_notified(history: List[Dict]):
    def enrich(value):
        if value:
            committee = WTOCommittee.objects.get(id=value)
            return {
                "id": str(committee.id),
                "name": committee.name,
            }
        return value

    for item in history:
        if item["field"] != "committee_notified":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_impact(history: List[Dict]):
    def enrich(value):
        if value:
            return {"code": value, "name": ECONOMIC_ASSESSMENT_IMPACT[value]}

    for item in history:
        if item["field"] != "impact":
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


def enrich_time_to_resolve(history: List[Dict]):
    def enrich(value):
        if value:
            return {"id": value, "name": RESOLVABILITY_ASSESSMENT_TIME[value]}

    for item in history:
        if item["field"] != "time_to_resolve":
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


def enrich_effort_to_resolve(history: List[Dict]):
    def enrich(value):
        if value:
            return {"id": value, "name": RESOLVABILITY_ASSESSMENT_EFFORT[value]}

    for item in history:
        if item["field"] != "effort_to_resolve":
            continue
        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_scale_history(history: List[Dict]):
    def enrich(value):
        if value:
            return {"id": value, "name": STRATEGIC_ASSESSMENT_SCALE[value]}

    for item in history:
        if item["field"] != "scale":
            continue
        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_location(history: List[Dict]):
    def enrich(value):
        if value:
            return get_location_text(
                country_id=value["country"],
                trading_bloc=value["trading_bloc"],
                caused_by_trading_bloc=value["caused_by_trading_bloc"],
            )
        return value

    for item in history:
        if item["field"] != "country":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_sectors(history: List[Dict]):
    def enrich(value):
        if value and value.get("sectors"):
            enriched_sector_list = []
            for sector in value["sectors"]:
                enriched_sector_list.append(str(sector))
            value["sectors"] = enriched_sector_list
        return value

    for item in history:
        if item["field"] != "sectors":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_publish_status(history: List[Dict]):
    def enrich(value):
        status_text = PublicBarrierStatus.choices[value]
        return status_text

    for item in history:
        if item["field"] != "_public_view_status":
            continue

        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_public_barrier_status(history: List[Dict]):
    def enrich(value, set_to_none):
        value["is_resolved"] = "No"
        if value["status"] == 4:
            value["is_resolved"] = "Yes"
        if set_to_none:
            value["is_resolved"] = None
        return value

    # the first status history item needs to have None set
    # for is_resolved, so we need to determine the oldest entry
    first_status_history_date = datetime.now(UTC)
    for item in history:
        if item["field"] == "status" and item["date"] < first_status_history_date:
            first_status_history_date = item["date"]

    for item in history:
        if item["field"] != "status":
            continue

        set_to_none = False
        if item["date"] == first_status_history_date:
            set_to_none = True

        item["old_value"] = enrich(item["old_value"], set_to_none)
        item["new_value"] = enrich(item["new_value"], False)


def enrich_team_member_user(history: List[Dict]):
    def enrich(value) -> Optional[Dict]:
        if value["user"] is None:
            return

        User = namedtuple("User", ("first_name", "last_name", "email", "username"))
        user = User(
            value["user__first_name"],
            value["user__last_name"],
            value["user__email"],
            value["user__username"],
        )

        return {
            "user": {"id": value["user"], "name": cleansed_username(user)},
            "role": value["role"],
        }

    for item in history:
        if item["field"] != "user":
            continue
        item["old_value"] = enrich(item["old_value"])
        item["new_value"] = enrich(item["new_value"])


def enrich_action_plan(history: List[Dict]):
    def enrich(value):
        if value["owner__first_name"] and value["owner__last_name"]:
            full_name = value["owner__first_name"] + " " + value["owner__last_name"]
            return full_name

        # If there was no result, there was no ID the
        # action plan was previously owned by or is going to be owned by
        return None

    cleaned_history = []

    for item in history:
        # Enrich owner field
        if item["field"] == "owner__id":
            # History contains records where value has not changed, if we come
            # across one we need to discount it from the history list
            if item["old_value"] == item["new_value"]:
                continue
            else:
                item["old_value"] = enrich(item["old_value"])
                item["new_value"] = enrich(item["new_value"])
                item["field"] = "owner"
                cleaned_history.append(item)

        # Enrich strategic context field
        if item["field"] == "strategic_context":
            # Strategic Context contains records where value has been instantiated,
            # if we come across one we need to discount it from the history list
            if item["old_value"] is None and item["new_value"] == "":
                continue
            else:
                cleaned_history.append(item)

    # Overwrite the passed history list with the cleaned version
    history[:] = cleaned_history


def enrich_action_plan_task(history: List[Dict]):
    def enrich_assigned_to(value):
        if value["assigned_to__first_name"] and value["assigned_to__last_name"]:
            full_name = (
                value["assigned_to__first_name"] + " " + value["assigned_to__last_name"]
            )
            return full_name

        # If there was no result, there was no ID the
        # action plan was previously assigned to or is being assigned to
        return None

    def enrich_action_type(value):
        if value is not None:
            action_type = value.replace("_", " ").lower().capitalize()
            return action_type
        else:
            return None

    for item in history:
        # Enrich assigned_to field
        if item["field"] == "assigned_to__first_name":
            item["old_value"] = enrich_assigned_to(item["old_value"])
            item["new_value"] = enrich_assigned_to(item["new_value"])
            item["field"] = "assigned_to"
        # Enrich action_type field
        if item["field"] == "action_type":
            item["old_value"] = enrich_action_type(item["old_value"])
            item["new_value"] = enrich_action_type(item["new_value"])


def enrich_delivery_confidence(history: List[Dict]):
    def enrich(value):
        value["summary"] = value.pop("update")
        if value["status"] is not None:
            value["status"] = value["status"].replace("_", " ").lower().capitalize()
        return value

    cleaned_history = []

    for item in history:
        # Existing functionality for Delivery Confidence history items
        # is to display only when the status of a progress update has
        # changed, not the summary - so we need to remove any items where
        # status is the same across both old_value and new_value
        if item["old_value"]["status"] == item["new_value"]["status"]:
            continue
        else:
            item["old_value"] = enrich(item["old_value"])
            item["new_value"] = enrich(item["new_value"])
            cleaned_history.append(item)

    # Overwrite the passed history list with the cleaned version
    history[:] = cleaned_history
