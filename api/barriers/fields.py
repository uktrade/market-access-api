from rest_framework import serializers

from api.barriers.helpers import get_or_create_public_barrier
from api.barriers.models import BarrierCommodity
from api.commodities.models import Commodity
from api.commodities.serializers import BarrierCommoditySerializer
from api.core.utils import cleansed_username, sort_list_of_dicts
from api.interactions.models import Document
from api.metadata.constants import (
    BARRIER_ARCHIVED_REASON,
    BARRIER_PENDING,
    BARRIER_SOURCE,
    BARRIER_TERMS,
    STAGE_STATUS,
    TRADE_CATEGORIES,
    TRADE_DIRECTION_CHOICES,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.metadata.models import (
    BarrierPriority,
    BarrierTag,
    ExportType,
    Organisation,
    PolicyTeam,
)
from api.metadata.serializers import (
    BarrierPrioritySerializer,
    BarrierTagSerializer,
    ExportTypeSerializer,
    OrganisationSerializer,
    PolicyTeamSerializer,
)
from api.metadata.utils import (
    get_country,
    get_overseas_region,
    get_sector,
    get_trading_bloc,
)
from api.wto.models import WTOProfile
from api.wto.serializers import WTOProfileSerializer


class ArchivedField(serializers.BooleanField):
    def custom_update(self, validated_data):
        instance = self.parent.instance
        user = self.parent.context["request"].user
        archived = validated_data.pop("archived")

        if instance.archived is False and archived is True:
            instance.archive(
                user=user,
                reason=validated_data.pop("archived_reason", ""),
                explanation=validated_data.pop("archived_explanation", ""),
            )
        elif instance.archived is True and archived is False:
            instance.unarchive(
                user=user,
                reason=validated_data.pop("unarchived_reason", ""),
            )


class ArchivedReasonField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=BARRIER_ARCHIVED_REASON, **kwargs)

    def to_representation(self, value):
        reason_lookup = dict(BARRIER_ARCHIVED_REASON)
        return {
            "code": value,
            "name": reason_lookup.get(value),
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


class PolicyTeamsField(serializers.ListField):
    def to_representation(self, value):
        serializer = PolicyTeamSerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        return PolicyTeam.objects.filter(id__in=data)


class OrganisationsField(serializers.ListField):
    def to_representation(self, value):
        serializer = OrganisationSerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        return Organisation.objects.filter(id__in=data)


class CommoditiesField(serializers.ListField):
    def to_representation(self, value):
        serializer = BarrierCommoditySerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        serializer = BarrierCommoditySerializer(partial=self.parent.partial, many=True)
        return serializer.to_internal_value(data)

    def custom_update(self, validated_data):
        commodities_data = validated_data.pop("barrier_commodities")

        added_commodities = []

        for commodity_data in commodities_data:
            code = commodity_data.get("code").ljust(10, "0")
            country = commodity_data.get("country")
            trading_bloc = commodity_data.get("trading_bloc", "")
            hs6_code = code[:6].ljust(10, "0")
            commodity = Commodity.objects.filter(code=hs6_code, is_leaf=True).latest(
                "version"
            )
            barrier_commodity, created = BarrierCommodity.objects.get_or_create(
                barrier=self.parent.instance,
                commodity=commodity,
                code=code,
                country=country,
                trading_bloc=trading_bloc,
            )
            added_commodities.append(barrier_commodity.id)

        BarrierCommodity.objects.filter(barrier=self.parent.instance).exclude(
            id__in=added_commodities
        ).delete()


class PublicEligibilityField(serializers.BooleanField):
    def custom_update(self, validated_data):
        public_eligibility = validated_data.get("public_eligibility")
        public_barrier, created = get_or_create_public_barrier(self.parent.instance)

        if public_eligibility is True and public_barrier._public_view_status in (
            PublicBarrierStatus.NOT_ALLOWED,
            PublicBarrierStatus.UNKNOWN,
        ):
            public_barrier.public_view_status = PublicBarrierStatus.ALLOWED
            public_barrier.save()
        else:
            public_barrier.public_view_status = PublicBarrierStatus.NOT_ALLOWED
            public_barrier.save()

        if "public_eligibility_summary" not in validated_data:
            validated_data["public_eligibility_summary"] = ""


class SectorsField(serializers.ListField):
    def to_representation(self, value):
        return [get_sector(str(sector_id)) for sector_id in value]


class SectorField(serializers.UUIDField):
    def to_representation(self, value):
        return get_sector(str(value))


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


class SubStatusField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=BARRIER_PENDING, **kwargs)

    def to_representation(self, value):
        sub_status_lookup = dict(BARRIER_PENDING)
        return {
            "code": value,
            "name": sub_status_lookup.get(value),
        }


class TagsField(serializers.ListField):
    def to_representation(self, value):
        serializer = BarrierTagSerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        try:
            return BarrierTag.objects.filter(id__in=data)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid tag ids")


class ExportTypesField(serializers.ListField):
    def to_representation(self, value):
        serializer = ExportTypeSerializer(value.all(), many=True)
        return serializer.data

    def to_internal_value(self, data):
        try:
            return ExportType.objects.filter(name__in=data)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid export types")


class ExportTypeReportField(ExportTypesField):
    def to_representation(self, value):
        return [export_type.name for export_type in value.all()]


class TermField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=BARRIER_TERMS, **kwargs)

    def to_representation(self, value):
        term_lookup = dict(BARRIER_TERMS)
        return {
            "id": value,
            "name": term_lookup.get(value, "Unknown"),
        }


class TradeCategoryField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=TRADE_CATEGORIES, **kwargs)

    def to_representation(self, value):
        if value:
            lookup = dict(TRADE_CATEGORIES)
            return {
                "id": value,
                "name": lookup.get(value),
            }


class TradeDirectionField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        return super().__init__(choices=TRADE_DIRECTION_CHOICES, **kwargs)

    def to_representation(self, value):
        trade_direction_lookup = dict(TRADE_DIRECTION_CHOICES)
        return {
            "id": value,
            "name": trade_direction_lookup.get(value),
        }


class UserField(serializers.Field):
    def to_representation(self, value):
        return {
            "id": value.id,
            "name": cleansed_username(value),
        }

    def to_internal_value(self, data):
        self.fail("read_only")


class WTOProfileField(serializers.Field):
    def to_representation(self, value):
        serializer = WTOProfileSerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        serializer = WTOProfileSerializer(partial=self.parent.partial)
        return serializer.to_internal_value(data)

    def custom_update(self, validated_data):
        wto_profile = validated_data.pop("wto_profile")

        if wto_profile:
            document_fields = ("committee_notification_document", "meeting_minutes")
            for field_name in document_fields:
                if field_name in self.parent.initial_data["wto_profile"]:
                    document_id = (
                        self.parent.initial_data["wto_profile"].get(field_name) or None
                    )
                    if document_id:
                        try:
                            Document.objects.get(pk=document_id)
                        except Document.DoesNotExist:
                            continue
                    wto_profile[f"{field_name}_id"] = document_id

            WTOProfile.objects.update_or_create(
                barrier=self.parent.instance, defaults=wto_profile
            )


class NoneToBlankCharField(serializers.CharField):
    """
    This field requires AllowNoneAtToRepresentationMixin to be used by the serializer
    """

    def to_representation(self, value):
        if value is not None:
            return str(value)
        else:
            return ""


class FilterableReadOnlyField(serializers.Field):
    def __init__(self, to_repr_keys=(), **kwargs):
        """
        Allows to use the same format with the ability to only include the keys needed for the given serializer.
        :param to_repr_keys: list of STR - used to filter in value to only include the keys listed
        """
        self.to_repr_keys = to_repr_keys
        super().__init__(**kwargs)

    def get_data(self, value):
        """To be implemented"""
        return {}

    def filter_dict(self, data):
        """
        Returns only the selected keys in to_repr_keys if data is a dict.
        """
        new_data = {}
        try:
            for k in data.keys():
                if k in self.to_repr_keys:
                    new_data.setdefault(k, data[k])
            return new_data
        except AttributeError:
            return data

    def filter_list_of_dicts(self, data):
        """
        Allows to filter keys of a list of dicts, similarly how filter_dict works.
        """
        new_data = []
        for d in data:
            new_data.append(self.filter_dict(d))
        return new_data

    def to_representation(self, value):
        data = self.get_data(value)
        if self.to_repr_keys:
            if isinstance(data, list):
                return self.filter_list_of_dicts(data)
            if isinstance(data, dict):
                return self.filter_dict(data)
        else:
            return data

    def to_internal_value(self, data):
        self.fail("read_only")


class ReadOnlyStatusField(FilterableReadOnlyField):
    """
    Field serializer to be used with read only status fields.
    """

    def get_data(self, value):
        return {"id": value, "name": BarrierStatus.name(value)}


class ReadOnlyCountryField(FilterableReadOnlyField):
    """
    Field serializer to be used with read only country fields.
    """

    def get_data(self, value):
        if value:
            value = str(value)
            country = get_country(value) or {}
            return {
                "id": value,
                "name": country.get("name"),
                "trading_bloc": country.get("trading_bloc"),
            }


class ReadOnlyTradingBlocField(FilterableReadOnlyField):
    def get_data(self, value):
        if value:
            return get_trading_bloc(value)


class ReadOnlySectorsField(FilterableReadOnlyField):
    """
    Field serializer to be used with read only sectors fields.
    """

    def __init__(self, to_repr_keys=(), sort=True, **kwargs):
        super().__init__(to_repr_keys, **kwargs)
        self.sort = sort

    def get_data(self, value):
        def sector_name(sid):
            sector = get_sector(str(sid)) or {}
            return sector.get("name")

        sectors = [
            {"id": str(sector_id), "name": sector_name(str(sector_id))}
            for sector_id in value
            if sector_name(str(sector_id))
        ]
        if not self.sort:
            # this is used to make sure the main sector is always first
            return sectors
        return sort_list_of_dicts(sectors, "name")


class ReadOnlyAllSectorsField(serializers.Field):
    """
    Field serializer to be used with read only all_sectors fields.
    """

    def to_representation(self, value):
        return value or False

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


class DisplayChoiceField(serializers.ChoiceField):
    def to_representation(self, obj):
        if obj == "" and self.allow_blank:
            return obj
        if obj in self._choices:
            return self._choices[obj]
        else:
            return "invalid choice"

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == "" and self.allow_blank:
            return ""

        for key, val in self._choices.items():
            if val == data:
                return key
        self.fail("invalid_choice", input=data)


class LineBreakCharField(serializers.CharField):
    def to_representation(self, value):
        # Convert the string value to a list of lines.
        return value.splitlines()

    def to_internal_value(self, data):
        # Convert the list of lines back to a single string value.
        return "\n".join(data)


class OverseasRegionsField(serializers.ListField):
    def to_representation(self, value):
        return [get_overseas_region(region_id) for region_id in value]


class TradingBlocsField(serializers.ListField):
    def to_representation(self, value):
        return [get_trading_bloc(str(trading_bloc_id)) for trading_bloc_id in value]


class CountriesField(serializers.ListField):
    def to_representation(self, value):
        return [get_country(str(country_id)) for country_id in value]
