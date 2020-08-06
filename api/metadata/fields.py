from rest_framework import serializers

from .constants import BARRIER_TYPE_CATEGORIES
from .utils import get_admin_area, get_country


class AdminAreasField(serializers.ListField):
    def to_representation(self, value):
        admin_areas = [get_admin_area(str(admin_area_id)) for admin_area_id in value]
        return [admin_area for admin_area in admin_areas if admin_area is not None]


class CategoryGroupField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=BARRIER_TYPE_CATEGORIES, **kwargs)

    def to_representation(self, value):
        group_lookup = dict(BARRIER_TYPE_CATEGORIES)
        return {
            "code": value,
            "name": group_lookup.get(value),
        }


class CountryField(serializers.UUIDField):
    def to_representation(self, value):
        return get_country(str(value))
