import itertools

from typing import List, Tuple, Dict, Optional, Union

from django.db.models import QuerySet


def convert_v2_history_to_legacy_object(items: List) -> List:
    """
    Converts v2 data dictionaries to a monkey patch class with 'data' property
    """
    v2_list = []
    for item in items:
        v2_list.extend(
            [
                type(
                    "HistoryItemMonkey",
                    (),
                    {
                        "data": {
                            "date": item["date"],
                            "field": k,
                            "model": item["model"],
                            "new_value": field["new"],
                            "old_value": field.get("old"),
                            "user": item["user"],
                        }
                    },
                )
                for k, field in item["fields"].items()
            ]
        )
    return v2_list


def get_model_history(
        qs: QuerySet,
        model: str,
        fields: Tuple[Union[str, List[str]], ...],  # fields can be grouped ie ['a', ['b', 'c'], 'd]
        track_first_item: bool = False
) -> List[Dict]:
    qs_fields = []
    for field in fields:
        if isinstance(field, list):
            qs_fields.extend(field)
        else:
            qs_fields.append(field)

    qs = qs.order_by("history_date").values(
        *qs_fields, "history_date", "history_user__id", "history_user__username"
    )

    count = qs.count()

    history = []

    if count <= 1:
        # No history
        return history

    previous_item = None

    for item in qs:
        if previous_item is None:
            # No history for first item
            previous_item = item
            continue

        for field in fields:
            change = {}
            if isinstance(field, list):
                any_grouped_field_has_change = False
                for f in field:
                    if item[f] != previous_item[f]:
                        any_grouped_field_has_change = True
                        break

                if any_grouped_field_has_change:
                    change['old_value'] = {}
                    change['new_value'] = {}

                    for f in field:
                        change['old_value'][f] = previous_item[f]
                        change['new_value'][f] = item[f]
            elif item[field] != previous_item[field]:
                change['old_value'] = previous_item[field]
                change['new_value'] = item[field]

            if change:
                history_item = {
                    "model": model,
                    "date": item["history_date"],
                    "field": field if isinstance(field, str) else field[0],
                    "user": {
                        "id": item["history_user__id"],
                        "name": item["history_user__username"],
                    } if item["history_user__id"] else None,
                    **change
                }
                history.append(history_item)

        previous_item = item

    return history
