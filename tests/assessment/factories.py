import random

import factory
from factory.fuzzy import FuzzyText

from api.assessment.models import Assessment, ResolvabilityAssessment, StrategicAssessment
from api.metadata.constants import (
    RESOLVABILITY_ASSESSMENT_EFFORT,
    RESOLVABILITY_ASSESSMENT_TIME,
    STRATEGIC_ASSESSMENT_SCALE,
)


class AssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assessment

    impact = "MEDIUMLOW"
    explanation = "Some explanation."


def get_time_to_resolve():
    choices = [choice[0] for choice in RESOLVABILITY_ASSESSMENT_TIME]
    return random.choice(choices)


def get_effort_to_resolve():
    choices = [choice[0] for choice in RESOLVABILITY_ASSESSMENT_EFFORT]
    return random.choice(choices)


def get_scale():
    choices = [choice[0] for choice in STRATEGIC_ASSESSMENT_SCALE]
    return random.choice(choices)


class ResolvabilityAssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResolvabilityAssessment

    time_to_resolve = get_time_to_resolve()
    effort_to_resolve = get_effort_to_resolve()
    explanation = "Some explanation."


class StrategicAssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StrategicAssessment

    hmg_strategy = FuzzyText()
    government_policy = FuzzyText()
    trading_relations = FuzzyText()
    uk_interest_and_security = FuzzyText()
    uk_grants = FuzzyText()
    competition = FuzzyText()
    additional_information = FuzzyText()
    scale = get_scale()
