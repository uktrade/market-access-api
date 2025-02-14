import factory

from api.metadata.constants import OrganisationType
from api.metadata.models import BarrierPriority, BarrierTag, Organisation, PolicyTeam


class BarrierTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BarrierTag

    id = factory.Sequence(lambda n: 50 + n)
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


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    name = factory.Sequence(lambda n: "Organisation {}".format(n + 1))
    organisation_type = OrganisationType.MINISTERIAL_DEPARTMENTS


class BarrierPolicyTeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PolicyTeam

    id = factory.Sequence(lambda n: 50 + n)
    title = factory.Sequence(lambda n: "Policy team {}".format(n + 1))
