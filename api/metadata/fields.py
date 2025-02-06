from rest_framework import serializers

from api.metadata.utils import get_admin_area, get_country, get_trading_bloc


class AdminAreasField(serializers.ListField):
    def to_representation(self, value):
        admin_areas = [get_admin_area(str(admin_area_id)) for admin_area_id in value]
        return [admin_area for admin_area in admin_areas if admin_area is not None]


class CountryField(serializers.UUIDField):
    def to_representation(self, value):
        return get_country(str(value))


class CountryListField(serializers.ListField):
    def to_representation(self, value):
        return [get_country(str(country_id)) for country_id in value]


class TradingBlocField(serializers.CharField):
    def to_representation(self, value):
        if value:
            return get_trading_bloc(value)
