import uuid

from django.utils.timezone import now

import factory
from freezegun import freeze_time
from factory.fuzzy import FuzzyChoice, FuzzyDate

from api.barriers.models import BarrierInstance


class UnresolvedReportFactory(factory.django.DjangoModelFactory):
    sectors = [
        "af959812-6095-e211-a939-e4115bead28a",
        "75debee7-a182-410e-bde0-3098e4f7b822",
        "9538cecc-5f95-e211-a939-e4115bead28a",
    ]
    countries = [
        "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc",
        "985f66a0-5d95-e211-a939-e4115bead28a",
        "1f0be5c4-5d95-e211-a939-e4115bead28a",
    ]

    id = factory.LazyFunction(uuid.uuid4)
    problem_status = FuzzyChoice([1, 2]).fuzz()
    status = 1
    export_country = FuzzyChoice(countries).fuzz()
    sectors_affected = True
    sectors = [FuzzyChoice(sectors).fuzz()]
    product = "Some product"
    source = "OTHER"
    other_source = "Other source"
    barrier_title = "Some title"
    eu_exit_related = FuzzyChoice([True, False]).fuzz()
    problem_description = "Some problem_description"
    next_steps_summary = "Next steps summary"
    created_on = now()

    class Meta:
        model = BarrierInstance
