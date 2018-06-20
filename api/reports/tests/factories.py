import factory
import factory.fuzzy

from api.metadata.constants import
from api.metadata.constants import (
    PROBLEM_STATUS_TYPES,
    ESTIMATED_LOSS_RANGE,
    STAGE_STATUS,
    ADV_BOOLEAN,
    GOVT_RESPONSE,
    PUBLISH_RESPONSE,
    REPORT_STATUS
)
from api.reports.models import Report, ReportStage, Stage


class ReportFactory(factory.django.DjangoModelFactory):
    problem_status = factory.fuzzy.FuzzyChoice(PROBLEM_STATUS_TYPES)
    is_emergency = False
    company_id
    company_name
    contact_id
    product
    commodity_codes
    export_country
    problem_description
    problem_impact
    estimated_loss_range
    other_companies_affected
    govt_response_requester
    is_confidential
    sensitivity_summary
    can_publish
    name
    summary
    is_resolved
    support_type

    class Meta:
        model = Report
