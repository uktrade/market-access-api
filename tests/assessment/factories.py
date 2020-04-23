import factory

from api.assessment.models import Assessment


class AssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assessment

    impact = "MEDIUMLOW"
    explanation = "Some explanation."
