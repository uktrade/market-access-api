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
            'non_null_field': 'is_emergency',
            'error_message': 'is_emergency can not be null, when problem_status is 3'
        },
        {
            'condition_field': 'is_politically_sensitive',
            'operator': operator.eq,
            'value': True,
            'non_null_field': 'political_sensitivity_summary',
            'error_message': 'political_sensitivity_summary can not be null, when is_politically_sensitive is True'
        },
        {
            'condition_field': 'is_commercially_sensitive',
            'operator': operator.eq,
            'value': True,
            'non_null_field': 'commercial_sensitivity_summary',
            'error_message': 'commercial_sensitivity_summary can not be null, when is_commercially_sensitive is True'
        },
        {
            'condition_field': 'has_legal_infringment',
            'operator': operator.eq,
            'value': 1,
            'non_null_field': 'wto_infingment',
            'error_message': 'wto_infingment can not be null, when has_legal_infringment is True'
        },
        {
            'condition_field': 'has_legal_infringment',
            'operator': operator.eq,
            'value': 1,
            'non_null_field': 'fta_infingment',
            'error_message': 'fta_infingment can not be null, when has_legal_infringment is True'
        },
        {
            'condition_field': 'has_legal_infringment',
            'operator': operator.eq,
            'value': 1,
            'non_null_field': 'other_infingment',
            'error_message': 'other_infingment can not be null, when has_legal_infringment is True'
        },
        {
            'condition_field': 'has_legal_infringment',
            'operator': operator.eq,
            'value': 1,
            'non_null_field': 'infringment_summary',
            'error_message': 'infringment_summary can not be null, when has_legal_infringment is True'
        },
        {
            'condition_field': 'other_companies_affected',
            'operator': operator.eq,
            'value': True,
            'non_null_field': 'other_companies_info',
            'error_message': 'other_companies_info can not be null, when other_companies_affected is True'
        },
        {
            'condition_field': 'is_resolved',
            'operator': operator.eq,
            'value': False,
            'non_null_field': 'support_type',
            'error_message': 'support_type can not be null, when is_resolved is True'
        },
        {
            'condition_field': 'is_resolved',
            'operator': operator.eq,
            'value': False,
            'non_null_field': 'steps_taken',
            'error_message': 'steps_taken can not be null, when is_resolved is True'
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

            if value is None:
                errors[field_name] = [self.message]

        for item in self.conditional_fields:
            field_name = item['non_null_field']
            condition_value = data_combiner.get_value(item['condition_field'])
            non_null_value = data_combiner.get_value(item['non_null_field'])
            relate = item['operator']
            value_to_check = item['value']
            print(
                f'condition_value {condition_value}, non_null_value {non_null_value}, relate {relate}, value_to_check {value_to_check}')
            print(relate(condition_value, value_to_check))
            if condition_value and relate(condition_value, value_to_check):
                if non_null_value is None:
                    errors[field_name] = [item['error_message']]

        # extra validators
        # extra_errors = self._run_extra_validators(data)
        # for field, field_errors in extra_errors.items():
        #     errors[field] += field_errors

        if errors:
            raise ValidationError(errors)
