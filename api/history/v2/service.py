import operator
from collections import namedtuple
from typing import Dict, List, Tuple, Union

from django.db.models import QuerySet

from api.history.v2.enrichment import (
    enrich_country,
    enrich_main_sector,
    enrich_priority_level,
    enrich_top_priority_status,
    enrich_trade_category,
)

FieldMapping = namedtuple("FieldMapping", "query_name name")


def convert_v2_history_to_legacy_object(items: List) -> List:
    """
    Converts v2 data dictionaries to a monkey patch class with 'data' property
    """
    return [type("HistoryItemMonkey", (), {"data": item}) for item in items]


def enrich_full_history(
    barrier_history: List[Dict],
    programme_fund_history: List[Dict],
    top_priority_summary_history: List[Dict],
) -> List[Dict]:
    enrich_country(barrier_history)
    enrich_trade_category(barrier_history)
    enrich_main_sector(barrier_history)
    enrich_priority_level(barrier_history)
    enrich_top_priority_status(barrier_history, top_priority_summary_history)

    enriched_history = (
        barrier_history + programme_fund_history + top_priority_summary_history
    )
    enriched_history.sort(key=operator.itemgetter("date"))

    return enriched_history


def get_model_history(  # noqa: C901
    qs: QuerySet,
    model: str,
    fields: Tuple[Union[str, FieldMapping, List[Union[str, FieldMapping]]], ...],
    track_first_item: bool = False,
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

    Returns:
        Returns a list of dictionaries representing the historical changes.
    """
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

    qs = qs.order_by("history_date").values(
        *qs_fields, "history_date", "history_user__id", "history_user__username"
    )

    count = qs.count()

    history = []

    if count <= 1 and not track_first_item:
        # No history
        return history

    previous_item = None

    for item in qs:
        if previous_item is None:
            if track_first_item:
                # Render first historical item in a table.
                change = {"old_value": None, "new_value": {}}
                for field in fields:
                    if isinstance(field, list):
                        for f in field:
                            change["old_value"][f] = None
                            change["new_value"][f] = item[f]
                    else:
                        change["old_value"] = None
                        change["new_value"] = item[field]

                    history.append(
                        {
                            "model": model,
                            "date": item["history_date"],
                            "field": (
                                field if isinstance(field, str) else field[0]
                            ).replace("_cache", ""),
                            "user": {
                                "id": item["history_user__id"],
                                "name": item["history_user__username"],
                            }
                            if item["history_user__id"]
                            else None,
                            **change,
                        }
                    )
            previous_item = item
            continue

        for field in fields:
            change = {}
            if isinstance(field, list):
                any_grouped_field_has_change = False
                for f in field:
                    name = f if isinstance(f, str) else f.query_name
                    if item[name] != previous_item[name]:
                        any_grouped_field_has_change = True
                        break

                if any_grouped_field_has_change:
                    change["old_value"] = {}
                    change["new_value"] = {}

                    for f in field:
                        # normalize all fields to FieldMapping
                        f = f if isinstance(f, FieldMapping) else FieldMapping(f, f)
                        change["old_value"][f.name] = previous_item[f.query_name]
                        change["new_value"][f.name] = item[f.query_name]
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
                            else field.name
                            if isinstance(field, FieldMapping)
                            else field[0].name
                            if isinstance(field[0], FieldMapping)
                            else field[0]
                        ).replace("_cache", ""),
                        "user": {
                            "id": item["history_user__id"],
                            "name": item["history_user__username"],
                        }
                        if item["history_user__id"]
                        else None,
                        **change,
                    }
                )

        previous_item = item

    return history
