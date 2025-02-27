"""
Converting legacy history to V2 example:

1) Extend the model with a get_history class method
    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(barrier__id=barrier_id)
        fields = ("stakeholders",)

        return get_model_history(
            qs,
            model="action_plan",
            fields=fields,
            track_first_item=True,
        )

2) Enrich the history - examples can be found in def get_full_history(). service.enrich_full_history() can be extended
with new history tables and custom in-memory enrichments can be added to service.enrichment.py. State of all the history
tables are shared in get_full_history()

Fields:
service.get_model_history() takes a list of fields to retrieve history for. These fields have 3 type:

str
    A single history field in 1 item

FieldMapping
    Convenience namdetuple mapping of a field using django query mechanics for foreign tables. (required by legacy)

    ie - FieldMapping("priority__code", "priority") retrieves the value from related table and sets the field name.

List[str, FieldMapping]
    A collection of history fields in 1 item.
"""

import operator
from collections import namedtuple
from typing import Dict, List, Optional, Tuple, Union

from django.db.models import QuerySet

from api.core.utils import pretty_sso_name
from api.history.v2.enrichment import (
    enrich_action_plan,
    enrich_action_plan_task,
    enrich_committee_notification_document,
    enrich_committee_notified,
    enrich_committee_raised_in,
    enrich_commodities,
    enrich_country,
    enrich_delivery_confidence,
    enrich_effort_to_resolve,
    enrich_impact,
    enrich_main_sector,
    enrich_meeting_minutes,
    enrich_preliminary_assessment,
    enrich_priority_level,
    enrich_public_barrier_location,
    enrich_public_barrier_publish_status,
    enrich_public_barrier_sectors,
    enrich_public_barrier_status,
    enrich_rating,
    enrich_scale_history,
    enrich_sectors,
    enrich_status,
    enrich_team_member_user,
    enrich_time_to_resolve,
    enrich_top_priority_status,
    enrich_trade_category,
    enrich_wto_notified_status,
)

FieldMapping = namedtuple("FieldMapping", ["query_name", "name"])


def convert_v2_history_to_legacy_object(items: List) -> List:
    """
    Converts v2 data dictionaries to a monkey patch class with 'data' property
    """
    return [type("HistoryItemMonkey", (), {"data": item}) for item in items]


def enrich_full_history(
    barrier_history: List[Dict],
    preliminary_assessment_history: List[Dict],
    programme_fund_history: List[Dict],
    top_priority_summary_history: List[Dict],
    wto_history: List[Dict],
    team_member_history: List[Dict],
    public_barrier_history: Union[List[Dict], None],
    economic_assessment_history: List[Dict],
    economic_impact_assessment_history: List[Dict],
    resolvability_assessment_history: List[Dict],
    strategic_assessment_history: List[Dict],
    action_plan_history: List[Dict],
    action_plan_task_history: List[Dict],
    action_plan_milestone_history: List[Dict],
    delivery_confidence_history: List[Dict],
    next_step_item_history: List[Dict],
    estimated_resolution_date_request_history: List[Dict],
) -> List[Dict]:
    """
    Enrichment pipeline for full barrier history.
    """
    enrich_country(barrier_history)
    enrich_preliminary_assessment(preliminary_assessment_history)
    enrich_trade_category(barrier_history)
    enrich_main_sector(barrier_history)
    enrich_priority_level(barrier_history)
    enrich_sectors(barrier_history)
    enrich_status(barrier_history)
    enrich_commodities(barrier_history)
    enrich_rating(economic_assessment_history)
    enrich_top_priority_status(
        barrier_history=barrier_history,
        top_priority_summary_history=top_priority_summary_history,
    )
    enrich_committee_notification_document(wto_history)
    enrich_committee_notified(wto_history)
    enrich_committee_raised_in(wto_history)
    enrich_meeting_minutes(wto_history)
    enrich_wto_notified_status(wto_history)
    enrich_team_member_user(team_member_history)

    if public_barrier_history:
        enrich_public_barrier_location(public_barrier_history)
        enrich_public_barrier_sectors(public_barrier_history)
        enrich_public_barrier_publish_status(public_barrier_history)
        enrich_public_barrier_status(public_barrier_history)

    enrich_impact(economic_impact_assessment_history)
    enrich_time_to_resolve(resolvability_assessment_history)
    enrich_effort_to_resolve(resolvability_assessment_history)
    enrich_scale_history(strategic_assessment_history)
    enrich_action_plan(action_plan_history)
    enrich_action_plan_task(action_plan_task_history)
    enrich_delivery_confidence(delivery_confidence_history)

    enriched_history = (
        barrier_history
        + preliminary_assessment_history
        + programme_fund_history
        + top_priority_summary_history
        + wto_history
        + team_member_history
        + (public_barrier_history or [])
        + economic_assessment_history
        + economic_impact_assessment_history
        + resolvability_assessment_history
        + strategic_assessment_history
        + action_plan_history
        + action_plan_task_history
        + action_plan_milestone_history
        + delivery_confidence_history
        + next_step_item_history
        + estimated_resolution_date_request_history
    )
    from pprint import pprint

    pprint(estimated_resolution_date_request_history)
    enriched_history.sort(key=operator.itemgetter("date"))

    return enriched_history


def flatten_fields(
    fields: Tuple[Union[str, FieldMapping, List[Union[str, FieldMapping]]], ...]
):
    qs_fields = []
    for field in fields:
        if isinstance(field, list):
            for f in field:
                if isinstance(f, FieldMapping):
                    qs_fields.append(f.query_name)
                else:
                    qs_fields.append(f)
        elif isinstance(field, FieldMapping):
            qs_fields.append(field.query_name)
        else:
            qs_fields.append(field)
    return qs_fields


def get_model_history(  # noqa: C901
    qs: QuerySet,
    model: str,
    fields: Tuple[Union[str, FieldMapping, List[Union[str, FieldMapping]]], ...],
    track_first_item: bool = False,
    primary_key: Optional[str] = None,
) -> List[Dict]:
    """
    This function returns the raw historical changes for a django-simple-history table.

    Args:
        qs: Queryset of historical table.
        model: Model name.
        fields: A List of fields to be returned. Fields can be grouped into list.
                    ie: [a, [b, c], d].
                        [b, c] will be considered a group, with `b` as the primary change. This was done for
                        backward compatibility with the legacy history FE.
        track_first_item: Track first item in table (typically for M2M fields)
        primary_key: Separate records by primary key

    Returns:
        Returns a list of dictionaries representing the historical changes.
    """
    flattened_fields = flatten_fields(fields)

    if primary_key and primary_key not in flattened_fields:
        flattened_fields.append(primary_key)

    qs = qs.order_by("history_date").values(
        *flattened_fields, "history_date", "history_user__id", "history_user__username"
    )

    return get_history_changes(qs, model, fields, track_first_item, primary_key)


def get_history_changes(  # noqa: C901
    qs, model, fields, track_first_item: bool = False, primary_key: Optional[str] = None
):
    count = qs.count() if isinstance(qs, QuerySet) else len(qs)

    history = []

    if count <= 1 and not track_first_item:
        # No history
        return history

    previous_item = None

    for item in qs:
        primary_field = {}
        if primary_key:
            primary_field[primary_key] = item[primary_key]

        if primary_key and previous_item:
            if previous_item[primary_key] != item[primary_key]:
                # If a new primary reference is found, treat it as the first item as its the first historical
                # change for the object with that key
                previous_item = None
        if previous_item is None:
            if track_first_item:
                # Render first historical item in a table.
                for field in fields:
                    change = {"old_value": None, "new_value": {}}
                    if isinstance(field, list):
                        if change["old_value"] is None:
                            change["old_value"] = {}
                        if change["new_value"] is None:
                            change["new_value"] = {}
                        for f in field:
                            f = f if isinstance(f, FieldMapping) else FieldMapping(f, f)
                            change["old_value"][f.name] = None
                            change["new_value"][f.name] = item[f.query_name]
                    else:
                        change["old_value"] = None
                        change["new_value"] = item[field]

                    history.append(
                        {
                            "model": model,
                            "date": item["history_date"],
                            "field": (
                                field
                                if isinstance(field, str)
                                else (
                                    field.name
                                    if isinstance(field, FieldMapping)
                                    else (
                                        field[0].name
                                        if isinstance(field[0], FieldMapping)
                                        else field[0]
                                    )
                                )  # field[0] - First field defined is the primary field name
                            ).replace("_cache", ""),
                            "user": (
                                {
                                    "id": item["history_user__id"],
                                    "name": pretty_sso_name(
                                        item["history_user__username"]
                                    ),
                                }
                                if item["history_user__id"]
                                else None
                            ),
                            **change,
                            **primary_field,
                        }
                    )
            previous_item = item
            continue

        for field in fields:
            change = {}
            if isinstance(field, list):
                any_grouped_field_has_change = False
                old_values, new_values = {}, {}
                for f in field:
                    name = f if isinstance(f, str) else f.query_name
                    if (
                        not any_grouped_field_has_change
                        and item[name] != previous_item[name]
                    ):
                        any_grouped_field_has_change = True

                    # normalize all fields to FieldMapping
                    f = f if isinstance(f, FieldMapping) else FieldMapping(f, f)
                    old_values[f.name] = previous_item[f.query_name]
                    new_values[f.name] = item[f.query_name]

                if any_grouped_field_has_change:
                    change["old_value"] = old_values
                    change["new_value"] = new_values

            elif item[field] != previous_item[field]:
                change["old_value"] = previous_item[field]
                change["new_value"] = item[field]

            if change:
                history.append(
                    {
                        "model": model,
                        "date": item["history_date"],
                        "field": (
                            field
                            if isinstance(field, str)
                            else (
                                field.name
                                if isinstance(field, FieldMapping)
                                else (
                                    field[0].name
                                    if isinstance(field[0], FieldMapping)
                                    else field[0]
                                )
                            )  # field[0] - First field defined is the primary field name
                        ).replace("_cache", ""),
                        "user": (
                            {
                                "id": item["history_user__id"],
                                "name": pretty_sso_name(item["history_user__username"]),
                            }
                            if item["history_user__id"]
                            else None
                        ),
                        **change,
                        **primary_field,
                    }
                )

        previous_item = item

    return history
