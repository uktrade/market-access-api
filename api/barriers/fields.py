from rest_framework import serializers

from api.metadata.utils import get_country


class CountryField(serializers.Field):
    def to_representation(self, value):
        return get_country(str(value))

    def to_internal_value(self, data):
        return data