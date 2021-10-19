from django.core.cache import cache

from api.assessment.automate.calculator import AssessmentCalculator
from api.barriers.models import Barrier


def calculate_barrier_economic_assessment(barrier_id: str):
    barrier = Barrier.objects.get(pk=barrier_id)
    assert barrier.country_name is not None
    assessment_calculator = AssessmentCalculator(cache=cache)
    commodity_codes = [c.trimmed_code for c in barrier.commodities.all()]
    return assessment_calculator.calculate(
        commodity_codes=commodity_codes,
        product=barrier.product,
        country1=barrier.country_name,
    )
