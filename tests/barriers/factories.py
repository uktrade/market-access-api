import datetime

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDate

from api.barriers.models import BarrierInstance


def fuzzy_sector():
    sectors = (
        "af959812-6095-e211-a939-e4115bead28a",     # Advanced Engineering
        "75debee7-a182-410e-bde0-3098e4f7b822",
        "9538cecc-5f95-e211-a939-e4115bead28a",
    )
    return FuzzyChoice(sectors).fuzz()


def fuzzy_country():
    countries = (
        "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc",
        "985f66a0-5d95-e211-a939-e4115bead28a",
        "1f0be5c4-5d95-e211-a939-e4115bead28a",
        "a05f66a0-5d95-e211-a939-e4115bead28a",
        "a75f66a0-5d95-e211-a939-e4115bead28a",
        "ad5f66a0-5d95-e211-a939-e4115bead28a",
    )
    return FuzzyChoice(countries).fuzz()


def fuzzy_date():
    return FuzzyDate(
        start_date=datetime.date.today() - datetime.timedelta(days=45),
        end_date=datetime.date.today(),
    ).evaluate(2, None, False)


class BarrierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BarrierInstance

    problem_status = FuzzyChoice([1, 2, 7]).fuzz()
    status = 1
    export_country = fuzzy_country()
    sectors_affected = True
    sectors = [fuzzy_sector()]
    product = factory.Sequence(lambda n: "Product {}".format(n + 1))
    source = "COMPANY"
    barrier_title = factory.Sequence(lambda n: "Barrier {}".format(n + 1))
    summary = "Some problem description."
    next_steps_summary = "Some steps to be taken."

    @factory.post_generation
    def convert_to_barrier(self, create, extracted, **kwargs):
        # a barrier is considered a report until it's submitted
        self.submit_report()

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of tags were passed in, use them
            self.tags.add(*extracted)


class ReportFactory(factory.django.DjangoModelFactory):
    """
    BarrierInstances are called Reports until they're submitted via self.submit_report()
    """
    class Meta:
        model = BarrierInstance

    draft = True
    archived = False
    problem_status = FuzzyChoice([1, 2, 7]).fuzz()
    status = 1
    export_country = fuzzy_country()
    sectors_affected = True
    sectors = [fuzzy_sector()]
    product = factory.Sequence(lambda n: "Product {}".format(n + 1))
    source = "COMPANY"
    barrier_title = factory.Sequence(lambda n: "Barrier {}".format(n + 1))
    summary = "Some problem description."
    next_steps_summary = "Some steps to be taken."

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of tags were passed in, use them
            self.tags.add(*extracted)
