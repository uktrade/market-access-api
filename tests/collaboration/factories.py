import factory

from api.collaboration.models import TeamMember


class TeamMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamMember
