from rest_framework import serializers

from api.barriers.helpers import get_or_create_public_barrier
from api.metadata.constants import BarrierStatus, PublicBarrierStatus, STAGE_STATUS
from api.metadata.utils import get_country, get_sector


class CountryField(serializers.Field):
    def to_representation(self, value):
        return get_country(str(value))

    def to_internal_value(self, data):
        return data


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
