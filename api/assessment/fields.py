from rest_framework import serializers

from api.metadata.constants import ASSESMENT_IMPACT


class ImpactField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=ASSESMENT_IMPACT, **kwargs)

    def to_representation(self, value):
        impact_lookup = dict(ASSESMENT_IMPACT)
        return {
            "code": value,
            "name": impact_lookup.get(value),
        }
