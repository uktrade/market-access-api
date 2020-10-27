from rest_framework import serializers

from api.metadata.constants import (
    ASSESMENT_EFFORT_TO_RESOLVE,
    ASSESMENT_IMPACT,
    ASSESMENT_TIME_TO_RESOLVE,
    STRATEGIC_ASSESSMENT_SCALE,
)


class ImpactField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=ASSESMENT_IMPACT, **kwargs)

    def to_representation(self, value):
        impact_lookup = dict(ASSESMENT_IMPACT)
        return {
            "code": value,
            "name": impact_lookup.get(value),
        }


class EffortToResolveField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=ASSESMENT_EFFORT_TO_RESOLVE, **kwargs)

    def to_representation(self, value):
        lookup = dict(ASSESMENT_EFFORT_TO_RESOLVE)
        return {
            "id": value,
            "name": lookup.get(value),
        }


class TimeToResolveField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=ASSESMENT_TIME_TO_RESOLVE, **kwargs)

    def to_representation(self, value):
        lookup = dict(ASSESMENT_TIME_TO_RESOLVE)
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
