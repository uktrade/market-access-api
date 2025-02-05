import factory

from api.barriers.models import Barrier, ProgrammeFundProgressUpdate
from api.metadata.constants import BARRIER_TYPE_CATEGORIES
from api.metadata.models import Category


class BarrierFactory(factory.django.DjangoModelFactory):
    term = 1
    status = 1
    country = "985f66a0-5d95-e211-a939-e4115bead28a"  # Angola
    trade_direction = 1
    sectors_affected = True
    sectors = ["af959812-6095-e211-a939-e4115bead28a"]
    product = "TEST PRODUCT"
    source = "COMPANY"
    title = "TEST BARRIER"
    summary = "Some problem description."
    next_steps_summary = "Some steps to be taken."
    top_priority_status = "NONE"
    main_sector = "355f977b-8ac3-e211-a646-e4115bead28a"  # Consumer and retail
    is_currently_active = True

    class Meta:
        model = Barrier


class ProgrammeFundProgressUpdateFactory(factory.django.DjangoModelFactory):
    milestones_and_deliverables = factory.Sequence(lambda n: "Product {}".format(n + 1))
    expenditure = factory.Sequence(lambda n: "Product {}".format(n + 1))

    class Meta:
        model = ProgrammeFundProgressUpdate
