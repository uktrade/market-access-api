import factory

from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    ProgrammeFundProgressUpdate,
)
from api.metadata.constants import BARRIER_TYPE_CATEGORIES, PROGRESS_UPDATE_CHOICES
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


class CategoryFactory(factory.django.DjangoModelFactory):
    category = BARRIER_TYPE_CATEGORIES.SERVICES

    class Meta:
        model = Category


class ProgrammeFundProgressUpdateFactory(factory.django.DjangoModelFactory):
    milestones_and_deliverables = factory.Sequence(lambda n: "Product {}".format(n + 1))
    expenditure = factory.Sequence(lambda n: "Product {}".format(n + 1))

    class Meta:
        model = ProgrammeFundProgressUpdate


class BarrierNextStepItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BarrierNextStepItem


class BarrierProgressUpdateFactory(factory.django.DjangoModelFactory):
    status = PROGRESS_UPDATE_CHOICES.ON_TRACK

    class Meta:
        model = BarrierProgressUpdate
