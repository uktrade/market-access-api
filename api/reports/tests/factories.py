import uuid

import factory
import factory.fuzzy

from api.metadata.constants import (
    ADV_BOOLEAN,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PROBLEM_STATUS_TYPES,
    PUBLISH_RESPONSE,
    REPORT_STATUS,
    STAGE_STATUS,
)
from api.reports.models import Report, ReportStage, Stage


class Stage1_1ReportFactory(factory.django.DjangoModelFactory):
    problem_status = factory.fuzzy.FuzzyChoice(PROBLEM_STATUS_TYPES)
    is_emergency = False
    company_id = factory.LazyFunction(uuid.uuid4)
    company_name = factory.Faker("text")
    company_sector = factory.LazyFunction(uuid.uuid4)
    contact_id = factory.LazyFunction(uuid.uuid4)

    class Meta:
        model = Report


class ReportFactory(factory.django.DjangoModelFactory):
    problem_status = factory.fuzzy.FuzzyChoice(PROBLEM_STATUS_TYPES)
    is_emergency = False
    # company_id
    # company_name
    # contact_id
    # product
    # commodity_codes
    # export_country
    # problem_description
    # problem_impact
    # estimated_loss_range
    # other_companies_affected
    # govt_response_requester
    # is_confidential
    # sensitivity_summary
    # can_publish
    # name
    # summary
    # is_resolved
    # support_type

    class Meta:
        model = Report
