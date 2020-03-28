import factory

from api.metadata.models import BarrierPriority, BarrierTag, Category


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Sequence(lambda n: "Category {}".format(n + 1))


class BarrierTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BarrierTag

    title = factory.Sequence(lambda n: "Tag {}".format(n + 1))


class BarrierPriorityFactory(factory.django.DjangoModelFactory):
    """
    BarrierPriority records are set by a migration file:
     - /api/metadata/migrations/0009_auto_20181205_1432.py
    """
    class Meta:
        model = BarrierPriority

    code = factory.Sequence(lambda n: "PRIO{}".format(n + 1))
    name = factory.Sequence(lambda n: "Priority {}".format(n + 1))
    order = factory.Sequence(lambda n: n + 1)
