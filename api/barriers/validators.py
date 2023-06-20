import logging
from collections import defaultdict

from rest_framework.exceptions import ValidationError

from api.barriers.report_stages import REPORT_CONDITIONS
from api.core.validate_utils import DataCombiner

logger = logging.getLogger(__name__)


class ReportReadyForSubmitValidator:
    """Validator which checks that the report has all detail fields filled in."""

    message = "This field is required."

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def __call__(self, data=None):  # noqa: C901
        # TODO: refactor to remove complexity
        """Validate that all the fields required are set."""
        data_combiner = DataCombiner(self.instance, data)

        errors = defaultdict(list)

        for stage in REPORT_CONDITIONS:
            # direct required fields
            for field_name in stage["required"]:
                value = data_combiner.get_value(field_name)

                if value is None:
                    errors[field_name] = [self.message]

            for item in stage["conditional"]:
                condition_value = data_combiner.get_value(item["condition_field"])
                relate = item["operator"]
                value_to_check = item["value"]

                if "non_null_field" in item:
                    if condition_value and relate(value_to_check, condition_value):
                        non_null_value = data_combiner.get_value(item["non_null_field"])
                        if non_null_value is None:
                            field_name = item["non_null_field"]
                            errors[field_name] = [item["error_message"]]
                elif not relate(value_to_check, condition_value):
                    field_name = item["condition_field"]
                    errors[field_name] = [item["error_message"]]

        if errors:
            raise ValidationError(errors)
