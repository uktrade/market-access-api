from rest_framework import serializers

from api.barriers.helpers import get_or_create_public_barrier
from api.core.utils import cleansed_username
from api.metadata.constants import (
    BARRIER_SOURCE,
    BarrierStatus,
    PublicBarrierStatus,
    STAGE_STATUS,
    PROBLEM_STATUS_TYPES,
)
from api.metadata.models import BarrierPriority, BarrierTag, Category
from api.metadata.serializers import BarrierPrioritySerializer, BarrierTagSerializer, CategorySerializer
from api.metadata.utils import get_admin_area, get_country, get_sector


class AdminAreasField(serializers.ListField):
    def to_representation(self, value):
        admin_areas = [get_admin_area(str(admin_area_id)) for admin_area_id in value]
        return [admin_area for admin_area in admin_areas if admin_area is not None]


class CategoriesField(serializers.ListField):
    def to_representation(self, value):
        serializer = CategorySerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        return Category.objects.filter(id__in=data)


class CountryField(serializers.UUIDField):
    def to_representation(self, value):
        return get_country(str(value))


class ScopeField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=PROBLEM_STATUS_TYPES, **kwargs)

    def to_representation(self, value):
        scope_lookup = dict(PROBLEM_STATUS_TYPES)
        return {
            "id": value,
            "name": scope_lookup.get(value, "Unknown"),
        }


class SectorsField(serializers.ListField):
    def to_representation(self, value):
        return [get_sector(str(sector_id)) for sector_id in value]


class SourceField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=BARRIER_SOURCE, **kwargs)

    def to_representation(self, value):
        source_lookup = dict(BARRIER_SOURCE)
        return {
            "code": value,
            "name": source_lookup.get(value, "Unknown"),
        }


class StatusField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=BarrierStatus.choices, **kwargs)

    def to_representation(self, value):
        status_lookup = dict(BarrierStatus.choices)
        return {
            "id": value,
            "name": status_lookup.get(value, "Unknown"),
        }


class BarrierPriorityField(serializers.Field):
    def to_representation(self, value):
        serializer = BarrierPrioritySerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        try:
            return BarrierPriority.objects.get(code=data)
        except BarrierPriority.DoesNotExist:
            raise serializers.ValidationError("Priority not found")


class TagsField(serializers.ListField):
    def to_representation(self, value):
        serializer = BarrierTagSerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        try:
            return BarrierTag.objects.filter(id__in=data)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid tag ids")


class UsernameField(serializers.Field):
    def to_representation(self, value):
        return cleansed_username(value)

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class PublicEligibilityField(serializers.BooleanField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        public_barrier, created = get_or_create_public_barrier(self.parent.instance)

        if value is True and public_barrier._public_view_status in (
            PublicBarrierStatus.INELIGIBLE,
            PublicBarrierStatus.UNKNOWN,
        ):
            public_barrier.public_view_status = PublicBarrierStatus.ELIGIBLE
            public_barrier.save()
        elif value is False:
            public_barrier.public_view_status = PublicBarrierStatus.INELIGIBLE
            public_barrier.save()

        return value


class NoneToBlankCharField(serializers.CharField):

    def to_representation(self, value):
        if value is not None:
            return str(value)
        else:
            return ""


class ReadOnlyStatusField(serializers.Field):
    """
    Field serializer to be used with read only status fields.
    """

    def to_representation(self, value):
        return {
            "id": value,
            "name": BarrierStatus.name(value)
        }

    def to_internal_value(self, data):
        self.fail("read_only")


class ReadOnlyCountryField(serializers.Field):
    """
    Field serializer to be used with read only country / export_country fields.
    """

    def to_representation(self, value):
        value = str(value)
        country = get_country(value) or {}
        return {
            "id": value,
            "name": country.get("name")
        }

    def to_internal_value(self, data):
        self.fail("read_only")


class ReadOnlySectorsField(serializers.Field):
    """
    Field serializer to be used with read only sectors fields.
    """

    def to_representation(self, value):
        def sector_name(sid):
            sector = get_sector(str(sid)) or {}
            return sector.get("name")

        return [
            {"id": str(sector_id), "name": sector_name(str(sector_id))}
            for sector_id in value
            if sector_name(str(sector_id))
        ]

    def to_internal_value(self, data):
        self.fail("read_only")


class ReadOnlyAllSectorsField(serializers.Field):
    """
    Field serializer to be used with read only all_sectors fields.
    """

    def to_representation(self, value):
        return value or False

    def to_internal_value(self, data):
        self.fail("read_only")


class ReadOnlyCategoriesField(serializers.Field):
    """
    Field serializer to be used with read only categories fields.
    """

    def to_representation(self, value):
        return [
            {"id": category.id, "title": category.title}
            for category in value.all()
        ]

    def to_internal_value(self, data):
        self.fail("read_only")


class BarrierReportStageListingField(serializers.RelatedField):
    def to_representation(self, value):
        stage_status_dict = dict(STAGE_STATUS)
        return {
            "stage_code": value.stage.code,
            "stage_desc": value.stage.description,
            "status_id": value.status,
            "status_desc": stage_status_dict[value.status],
        }
