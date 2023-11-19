from typing import Tuple, List

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
                    'HistoryItemMonkey',
                    (),
                    {
                        "data": {
                            "date": item["date"],
                            "field": k,
                            "model": item["model"],
                            "new_value": field["new"],
                            "old_value": field.get("old"),
                            "user": item["user"]
                        }
                    }
                )
                for k, field in item["fields"].items()
            ]
        )
    return v2_list
    

def get_model_history(qs: QuerySet, model: str, fields: Tuple[str, ...], track_first_item: bool = False):
    qs = qs.order_by(
        "history_date"
    ).values(*fields, "history_date", "history_user__id", "history_user__username")

    count = qs.count()

    history = []

    if count == 0:
        # No history
        return history

    if not track_first_item and count == 1:
        # No history if the first item created should not be tracked
        # ie - m2m relation created during the construction of a draft barrier.
        return history

    previous_item = None

    for item in qs:
        if previous_item is None:
            if track_first_item:
                # Append the first item as a historical change
                history.append({
                    "model": model,
                    "date": item["history_date"],
                    "fields": {field: {"new": item[field]} for field in fields},
                    "user": {"id": item["history_user__id"], "name": item["history_user__username"]}
                })

            # Set the to compare to the previous historical item
            previous_item = item
            continue

        changed_fields = {}
        for field in fields:
            if item[field] != previous_item[field]:
                changed_fields[field] = {"new": item[field], "old": previous_item[field]}

        history_item = {
            "model": model,
            "date": item["history_date"],
            "fields": changed_fields,
            "user": {"id": item["history_user__id"], "name": item["history_user__username"]}
        }

        history.append(history_item)
        previous_item = item

    return history
