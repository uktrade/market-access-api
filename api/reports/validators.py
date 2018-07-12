import operator
from collections import defaultdict

from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from api.core.validate_utils import DataCombiner
from api.reports.stage_fields import REPORT_CONDITIONS


class StageCompleteValidator:
    """
    Validator checking if a stage is complete
    with all mandatory and conditional fields are filled in
    """


class ReportCompleteValidator:
    """Validator which checks that the report has all detail fields filled in."""

    # extra_validators = (
    #     ConditionalFieldsFilledInValidator(),
    # )

    message = "This field is required."

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

        for stage in REPORT_CONDITIONS:
            # direct required fields
            for field_name in stage["required"]:
                field = meta.get_field(field_name)

                if isinstance(field, models.ManyToManyField):
                    value = data_combiner.get_value_to_many(field_name)
                else:
                    value = data_combiner.get_value(field_name)

                if value is None:
                    errors[field_name] = [self.message]

            for item in stage["conditional"]:
                field_name = item["non_null_field"]
                condition_value = data_combiner.get_value(item["condition_field"])
                non_null_value = data_combiner.get_value(item["non_null_field"])
                relate = item["operator"]
                value_to_check = item["value"]
                if condition_value and relate(condition_value, value_to_check):
                    if non_null_value is None:
                        errors[field_name] = [item["error_message"]]

        # extra validators
        # extra_errors = self._run_extra_validators(data)
        # for field, field_errors in extra_errors.items():
        #     errors[field] += field_errors

        if errors:
            raise ValidationError(errors)
