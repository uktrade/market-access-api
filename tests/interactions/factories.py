import factory

from api.interactions.models import Interaction


class InteractionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Interaction

    kind ="COMMENT"
