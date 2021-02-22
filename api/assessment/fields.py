from rest_framework import serializers

from api.metadata.constants import (
    ECONOMIC_ASSESSMENT_IMPACT,
    ECONOMIC_ASSESSMENT_RATING,
    RESOLVABILITY_ASSESSMENT_EFFORT,
    RESOLVABILITY_ASSESSMENT_TIME,
    STRATEGIC_ASSESSMENT_SCALE,
)


class ImpactField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=ECONOMIC_ASSESSMENT_IMPACT, **kwargs)

    def to_representation(self, value):
        if value:
            lookup = dict(ECONOMIC_ASSESSMENT_IMPACT)
            return {"id": value, "name": lookup.get(int(value))}


class RatingField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=ECONOMIC_ASSESSMENT_RATING, **kwargs)

    def to_representation(self, value):
        if value:
            lookup = dict(ECONOMIC_ASSESSMENT_RATING)
            return {
                "code": value,
                "name": lookup.get(value),
            }


class EffortToResolveField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=RESOLVABILITY_ASSESSMENT_EFFORT, **kwargs)

    def to_representation(self, value):
        lookup = dict(RESOLVABILITY_ASSESSMENT_EFFORT)
        return {
            "id": value,
            "name": lookup.get(value),
        }


class TimeToResolveField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=RESOLVABILITY_ASSESSMENT_TIME, **kwargs)

    def to_representation(self, value):
        lookup = dict(RESOLVABILITY_ASSESSMENT_TIME)
        return {
            "id": value,
            "name": lookup.get(value),
        }


class StrategicAssessmentScaleField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=STRATEGIC_ASSESSMENT_SCALE, **kwargs)

    def to_representation(self, value):
        lookup = dict(STRATEGIC_ASSESSMENT_SCALE)
        return {
            "id": value,
            "name": lookup.get(value),
        }
