import logging

from hashid_field.rest import HashidSerializerCharField
from rest_framework import serializers

from api.barriers.fields import (
    DisplayChoiceField,
    NoneToBlankCharField,
    ReadOnlyAllSectorsField,
    ReadOnlyCountryField,
    ReadOnlySectorsField,
    ReadOnlyStatusField,
    ReadOnlyTradingBlocField,
    SectorField,
)
from api.barriers.models import PublicBarrier
from api.barriers.serializers.mixins import LocationFieldMixin
from api.core.serializers.mixins import AllowNoneAtToRepresentationMixin
from api.interactions.models import PublicBarrierNote
from api.interactions.serializers import PublicBarrierNoteSerializer
from api.metadata.constants import PublicBarrierStatus
from api.metadata.fields import TradingBlocField
from api.metadata.serializers import OrganisationSerializer

logger = logging.getLogger(__name__)

PUBLIC_ID = "barriers.PublicBarrier.id"


class NestedPublicBarrierSerializer(serializers.ModelSerializer):
    """
    Simple serializer for use within BarrierDetailSerializer.
    """

    id = HashidSerializerCharField(source_field=PUBLIC_ID, read_only=True)
    title = NoneToBlankCharField()
    summary = NoneToBlankCharField()
    unpublished_changes = serializers.SerializerMethodField()
    changed_since_published = serializers.SerializerMethodField()
    public_view_status_display = DisplayChoiceField(
        source="public_view_status", choices=PublicBarrierStatus.choices
    )
    set_to_allowed_on = serializers.SerializerMethodField()

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "public_view_status",
            "public_view_status_display",
            "title",
            "summary",
            "unpublished_changes",
            "changed_since_published",
            "last_published_on",
            "set_to_allowed_on",
        )

    def get_set_to_allowed_on(self, obj):
        if obj.set_to_allowed_on:
            return obj.set_to_allowed_on.strftime("%Y-%m-%d")

    def get_unpublished_changes(self, obj):
        return bool(obj.unpublished_changes)

    def get_changed_since_published(self, obj):
        return obj.changed_since_published


class PublicBarrierSerializer(
    AllowNoneAtToRepresentationMixin, serializers.ModelSerializer
):
    """
    Generic serializer for barrier public data.
    """

    id = HashidSerializerCharField(source_field=PUBLIC_ID, read_only=True)
    title = NoneToBlankCharField()
    summary = NoneToBlankCharField()
    internal_government_organisations = serializers.SerializerMethodField()
    status = ReadOnlyStatusField()
    country = ReadOnlyCountryField()
    trading_bloc = TradingBlocField()
    sectors = ReadOnlySectorsField()
    main_sector = SectorField()
    all_sectors = ReadOnlyAllSectorsField()
    latest_published_version = serializers.SerializerMethodField()
    unpublished_changes = serializers.SerializerMethodField()
    ready_to_be_published = serializers.SerializerMethodField()
    internal_code = serializers.SerializerMethodField()
    internal_id = serializers.SerializerMethodField()
    latest_note = serializers.SerializerMethodField()
    reported_on = serializers.DateTimeField()
    set_to_allowed_on = serializers.DateTimeField()

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "internal_code",
            "internal_id",
            "title",
            "title_updated_on",
            "internal_title_at_update",
            "summary",
            "summary_updated_on",
            "internal_summary_at_update",
            "approvers_summary",
            "publishers_summary",
            "status",
            "status_date",
            "is_resolved",
            "country",
            "trading_bloc",
            "location",
            "sectors",
            "main_sector",
            "all_sectors",
            "public_view_status",
            "first_published_on",
            "last_published_on",
            "unpublished_on",
            "set_to_allowed_on",
            "latest_published_version",
            "unpublished_changes",
            "ready_to_be_published",
            "internal_government_organisations",
            "latest_note",
            "reported_on",
        )
        read_only_fields = (
            "id",
            "internal_code",
            "internal_id",
            "title_updated_on",
            "internal_title_at_update",
            "summary_updated_on",
            "internal_summary_at_update",
            "status",
            "status_date",
            "is_resolved",
            "country",
            "trading_bloc",
            "location",
            "sectors",
            "main_sector",
            "all_sectors",
            "public_view_status",
            "first_published_on",
            "last_published_on",
            "unpublished_on",
            "latest_published_version",
            "unpublished_changes",
            "ready_to_be_published",
            "internal_government_organisations",
            "latest_note",
            "reported_on",
        )

    def get_latest_published_version(self, obj):
        return PublishedVersionSerializer(obj.latest_published_version).data

    def get_unpublished_changes(self, obj):
        return obj.unpublished_changes

    def get_ready_to_be_published(self, obj):
        return obj.ready_to_be_published

    def get_internal_code(self, obj):
        return obj.barrier.code

    def get_internal_id(self, obj):
        return obj.barrier_id

    def get_internal_government_organisations(self, obj):
        return OrganisationSerializer(obj.barrier.organisations, many=True).data

    def get_latest_note(self, obj):
        try:
            # We need to perform Python sorting instead of SQL
            # as otherwise the prefetch would not get used
            note = sorted(
                list(obj.notes.all()), key=lambda note: note.created_on, reverse=True
            )[0]
            return PublicBarrierNoteSerializer(note).data
        except IndexError:
            return None
        except PublicBarrierNote.DoesNotExist:
            return None


class PublishedVersionSerializer(
    LocationFieldMixin, AllowNoneAtToRepresentationMixin, serializers.ModelSerializer
):
    """
    Serializer to be used with DMAS FE app
    """

    id = serializers.CharField()
    title = serializers.CharField()
    summary = serializers.CharField()
    is_resolved = serializers.BooleanField()
    country = ReadOnlyCountryField()
    location = serializers.CharField()
    sectors = ReadOnlySectorsField()
    main_sector = SectorField()
    all_sectors = ReadOnlyAllSectorsField()

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "title",
            "summary",
            "is_resolved",
            "status_date",
            "country",
            "location",
            "sectors",
            "all_sectors",
            "main_sector",
        )


class PublicPublishedVersionSerializer(
    LocationFieldMixin, AllowNoneAtToRepresentationMixin, serializers.ModelSerializer
):
    """
    Serializer to be used with gov.uk (public data)
    """

    id = HashidSerializerCharField(source_field=PUBLIC_ID, read_only=True)
    title = serializers.CharField()
    summary = serializers.CharField()
    country = ReadOnlyCountryField(to_repr_keys=("name", "trading_bloc"))
    trading_bloc = ReadOnlyTradingBlocField()
    sectors = serializers.SerializerMethodField()
    reported_on = serializers.DateTimeField(source="barrier.created_on")

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "title",
            "summary",
            "is_resolved",
            "status_date",
            "country",
            "caused_by_trading_bloc",
            "trading_bloc",
            "location",
            "sectors",
            "last_published_on",
            "reported_on",
        )

    def get_sectors(self, obj):
        if obj.all_sectors:
            return [{"name": "All sectors"}]
        else:
            # we need to add the main sector into the list as the first field of the array
            sectors = [obj.main_sector] + obj.sectors
            return ReadOnlySectorsField(
                to_repr_keys=("name",), sort=False
            ).to_representation(sectors)
