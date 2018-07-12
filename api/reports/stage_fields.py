import operator

from django.db import models

from api.core.validate_utils import DataCombiner

REPORT_CONDITIONS = [
    {
        "stage": "1.1",
        "order": 1,
        "required": ["problem_status"],
        "conditional": [
            {
                "condition_field": "problem_status",
                "operator": operator.gt,
                "value": 2,
                "non_null_field": "is_emergency",
                "error_message": "is_emergency can not be null, when problem_status is 3",
            }
        ],
    },
    {
        "stage": "1.2",
        "order": 2,
        "required": ["company_id", "company_name"],
        "optional": ["company_sector"],
        "conditional": [],
    },
    {"stage": "1.3", "order": 3, "required": ["contact_id"], "conditional": []},
    {
        "stage": "1.4",
        "order": 4,
        "required": [
            "product",
            "export_country",
            "problem_description",
            "barrier_title",
        ],
        "conditional": [],
    },
    {
        "stage": "1.5",
        "order": 5,
        "required": [
            "problem_impact",
            "estimated_loss_range",
            "other_companies_affected",
        ],
        "conditional": [],
    },
    {
        "stage": "1.6",
        "order": 6,
        "required": ["has_legal_infringement"],
        "conditional": [
            {
                "condition_field": "has_legal_infringement",
                "operator": operator.eq,
                "value": 1,
                "non_null_field": "wto_infringement",
                "error_message": "wto_infringement can not be null, when has_legal_infringement is True",
            },
            {
                "condition_field": "has_legal_infringement",
                "operator": operator.eq,
                "value": 1,
                "non_null_field": "fta_infringement",
                "error_message": "fta_infringement can not be null, when has_legal_infringement is True",
            },
            {
                "condition_field": "has_legal_infringement",
                "operator": operator.eq,
                "value": 1,
                "non_null_field": "other_infringement",
                "error_message": "other_infringement can not be null, when has_legal_infringement is True",
            },
            {
                "condition_field": "has_legal_infringement",
                "operator": operator.eq,
                "value": 1,
                "non_null_field": "infringement_summary",
                "error_message": "infringement_summary can not be null, when has_legal_infringement is True",
            },
        ],
    },
    {"stage": "1.7", "order": 7, "required": ["barrier_type"], "conditional": []},
    {
        "stage": "2.1",
        "order": 8,
        "required": ["is_resolved", "is_politically_sensitive"],
        "conditional": [
            {
                "condition_field": "is_resolved",
                "operator": operator.eq,
                "value": True,
                "non_null_field": "resolved_date",
                "error_message": "resolved_date can not be null, when is_resolved is True",
            },
            {
                "condition_field": "is_resolved",
                "operator": operator.eq,
                "value": True,
                "non_null_field": "resolution_summary",
                "error_message": "resolution_summary can not be null, when is_resolved is True",
            },
            {
                "condition_field": "is_resolved",
                "operator": operator.eq,
                "value": False,
                "non_null_field": "support_type",
                "error_message": "support_type can not be null, when is_resolved is False",
            },
            {
                "condition_field": "is_resolved",
                "operator": operator.eq,
                "value": False,
                "non_null_field": "steps_taken",
                "error_message": "steps_taken can not be null, when is_resolved is False",
            },
            {
                "condition_field": "is_politically_sensitive",
                "operator": operator.eq,
                "value": True,
                "non_null_field": "political_sensitivity_summary",
                "error_message": "political_sensitivity_summary can not be null, when is_politically_sensitive is True",
            },
        ],
    },
    {
        "stage": "2.2",
        "order": 9,
        "required": [
            "govt_response_requested",
            "is_commercially_sensitive",
            "can_publish",
        ],
        "conditional": [
            {
                "condition_field": "is_commercially_sensitive",
                "operator": operator.eq,
                "value": True,
                "non_null_field": "commercial_sensitivity_summary",
                "error_message": "commercial_sensitivity_summary can not be null, when is_commercially_sensitive is True",
            }
        ],
    },
]


def required_field_value(instance, field_name):
    data_combiner = DataCombiner(instance, None)
    meta = instance._meta
    field = meta.get_field(field_name)

    if isinstance(field, models.ManyToManyField):
        value = data_combiner.get_value_to_many(field_name)
    else:
        value = data_combiner.get_value(field_name)

    if value is None:
        return False

    return True


def conditional_field_value(instance, rule_item):
    data_combiner = DataCombiner(instance, None)

    condition_value = data_combiner.get_value(rule_item["condition_field"])
    non_null_value = data_combiner.get_value(rule_item["non_null_field"])
    relate = rule_item["operator"]
    value_to_check = rule_item["value"]
    if condition_value and relate(condition_value, value_to_check):
        if non_null_value is None:
            return False

        return True


def stage_status(instance, stage_condition):
    status = []
    for field in stage_condition["required"]:
        status.append(required_field_value(instance, field))

    for item in stage_condition["conditional"]:
        status.append(conditional_field_value(instance, item))

    if True in set(status) and False in set(status):
        return (stage_condition["stage"], 2)
    elif True in set(status):
        return (stage_condition["stage"], 3)
    else:
        return (stage_condition["stage"], 1)
