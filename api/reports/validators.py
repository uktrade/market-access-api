import operator
from collections import defaultdict

from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from api.core.validate_utils import DataCombiner


class ReportDetailsFilledInValidator:
    """Validator which checks that the report has all detail fields filled in."""

    REQUIRED_FIELDS = (
        'problem_status',
        'company_id',
        'company_name',
        'company_sector',
        'contact_id',
        'product',
        'export_country',
        'problem_description',
        'barrier_title',
        'problem_impact',
        'estimated_loss_range',
        'other_companies_affected',
        'has_legal_infringment',
        'wto_infingment',
        'fta_infingment',
        'other_infingment',
        'infringment_summary',
        'barrier_type',
        'is_resolved',
        'support_type',
        'steps_taken',
        'is_politically_sensitive',
        'govt_response_requester',
        'is_commercially_sensitive',
        'can_publish',
    )

    conditional_fields = [
        {
            'condition_field': 'problem_status',
            'operator': operator.gt,
            'value': 2,
            'non_null_field': 'is_emergency'
        },
    ]

    # extra_validators = (
    #     ConditionalFieldsFilledInValidator(),
    # )

    message = 'This field is required.'

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    # def get_extra_validators(self):
    #     """
    #     Useful for subclassing or testing.

    #     :returns: the extra_validators.
    #     """
    #     return self.extra_validators

    # def _run_extra_validators(self, data):
    #     """
    #     Run the extra validators against the instance/data.

    #     :returns: errors dict, either filled in or empty
    #     """
    #     errors = defaultdict(list)
    #     for validator in self.get_extra_validators():
    #         validator.set_instance(self.instance)
    #         try:
    #             validator(data)
    #         except ValidationError as exc:
    #             for field, field_errors in exc.detail.items():
    #                 errors[field] += field_errors
    #     return errors

    def __call__(self, data=None):
        """Validate that all the fields required are set."""
        data_combiner = DataCombiner(self.instance, data)

        meta = self.instance._meta
        errors = defaultdict(list)

        # direct required fields
        for field_name in self.REQUIRED_FIELDS:
            field = meta.get_field(field_name)

            if isinstance(field, models.ManyToManyField):
                value = data_combiner.get_value_to_many(field_name)
            else:
                value = data_combiner.get_value(field_name)

            if not value:
                errors[field_name] = [self.message]

        for item in self.conditional_fields:
            condition_field = meta.get_field(item['condition_field'])
            condition_value = value = data_combiner.get_value(condition_field)
            non_null_field = meta.get_field(item['non_null_field'])
            non_null_value = data_combiner.get_value(non_null_field)
            relate = item['operator']
            value_to_check = item['value']
            if relate(condition_value, value_to_check):
                if not non_null_value:
                    message = f'when {condition_field} is {relate} {value_to_check} then {non_null_field} can not be null'
                    errors[field_name] = [self.message]

        # extra validators
        # extra_errors = self._run_extra_validators(data)
        # for field, field_errors in extra_errors.items():
        #     errors[field] += field_errors

        if errors:
            raise ValidationError(errors)
