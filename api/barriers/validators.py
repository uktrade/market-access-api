from collections import defaultdict

from django.db import models
from rest_framework.exceptions import ValidationError

from api.core.validate_utils import DataCombiner
from api.barriers.report_stages import REPORT_CONDITIONS


class ReportReadyForSubmitValidator:
    """Validator which checks that the report has all detail fields filled in."""

    message = "This field is required."

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

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

        sectors_affected = data_combiner.get_value('sectors_affected')
        all_sectors = data_combiner.get_value('all_sectors')
        sectors = data_combiner.get_value('sectors')

        if sectors_affected and all_sectors is None and sectors is None:
            errors['sectors'] = 'missing data'

        if sectors_affected and all_sectors and sectors:
            errors['sectors'] = 'conflicting input'

        if errors:
            raise ValidationError(errors)
