from hashid_field.rest import HashidSerializerCharField
from rest_framework import serializers

from api.barriers.fields import (
    DisplayChoiceField,
    NoneToBlankCharField,
    ReadOnlyAllSectorsField,
    ReadOnlyCategoriesField,
    ReadOnlyCountryField,
    ReadOnlySectorsField,
    ReadOnlyStatusField,
    ReadOnlyTradingBlocField,
    SectorField,
)
from api.barriers.helpers import get_published_public_barriers
from api.barriers.models import PublicBarrier, PublicBarrierLightTouchReviews
from api.barriers.serializers.mixins import LocationFieldMixin
from api.core.serializers.mixins import AllowNoneAtToRepresentationMixin
from api.interactions.models import PublicBarrierNote
from api.interactions.serializers import PublicBarrierNoteSerializer
from api.metadata.constants import PublicBarrierStatus
from api.metadata.fields import TradingBlocField
from api.metadata.serializers import OrganisationSerializer

PUBLIC_ID = "barriers.PublicBarrier.id"


class PublicBarrierLightTouchReviewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicBarrierLightTouchReviews
        fields = (
            "content_team_approval",
            "has_content_changed_since_approval",
            "hm_trade_commissioner_approval",
            "hm_trade_commissioner_approval_enabled",
            "government_organisation_approvals",
            "missing_government_organisation_approvals",
            "enabled",
        )
        read_only_fields = ("missing_government_organisation_approvals", "enabled")


class NestedPublicBarrierSerializer(serializers.ModelSerializer):
    """
    Simple serializer for use within BarrierDetailSerializer.
    """

    id = HashidSerializerCharField(source_field=PUBLIC_ID, read_only=True)
    title = NoneToBlankCharField()
    summary = NoneToBlankCharField()
    unpublished_changes = serializers.SerializerMethodField()
    public_view_status_display = DisplayChoiceField(
        source="public_view_status", choices=PublicBarrierStatus.choices
    )

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "public_view_status",
            "public_view_status_display",
            "title",
            "summary",
            "unpublished_changes",
            "last_published_on",
        )

    def get_unpublished_changes(self, obj):
        return obj.unpublished_changes


class PublicBarrierSerializer(
    AllowNoneAtToRepresentationMixin, serializers.ModelSerializer
):
    """
    Generic serializer for barrier public data.
    """

    id = HashidSerializerCharField(source_field=PUBLIC_ID, read_only=True)
    title = NoneToBlankCharField()
    summary = NoneToBlankCharField()
    internal_title_changed = serializers.SerializerMethodField()
    internal_summary_changed = serializers.SerializerMethodField()
    internal_government_organisations = serializers.SerializerMethodField()
    status = ReadOnlyStatusField()
    internal_status = ReadOnlyStatusField()
    country = ReadOnlyCountryField()
    internal_country = ReadOnlyCountryField()
    trading_bloc = TradingBlocField()
    internal_trading_bloc = TradingBlocField()
    sectors = ReadOnlySectorsField()
    internal_sectors = ReadOnlySectorsField()
    all_sectors = ReadOnlyAllSectorsField()
    internal_all_sectors = ReadOnlyAllSectorsField()
    categories = ReadOnlyCategoriesField()
    internal_categories = ReadOnlyCategoriesField()
    latest_published_version = serializers.SerializerMethodField()
    unpublished_changes = serializers.SerializerMethodField()
    ready_to_be_published = serializers.SerializerMethodField()
    internal_code = serializers.SerializerMethodField()
    internal_id = serializers.SerializerMethodField()
    latest_note = serializers.SerializerMethodField()
    reported_on = serializers.DateTimeField(source="internal_created_on")
    light_touch_reviews = PublicBarrierLightTouchReviewsSerializer()
    internal_main_sector = SectorField()

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "internal_code",
            "internal_id",
            "title",
            "title_updated_on",
            "internal_title_changed",
            "internal_title_at_update",
            "summary",
            "summary_updated_on",
            "internal_summary_changed",
            "internal_summary_at_update",
            "approvers_summary",
            "status",
            "internal_status",
            "internal_status_changed",
            "status_date",
            "internal_status_date",
            "internal_status_date_changed",
            "is_resolved",
            "internal_is_resolved",
            "internal_is_resolved_changed",
            "country",
            "internal_country",
            "internal_country_changed",
            "trading_bloc",
            "internal_trading_bloc",
            "internal_trading_bloc_changed",
            "location",
            "internal_location",
            "internal_location_changed",
            "sectors",
            "internal_sectors",
            "internal_sectors_changed",
            "all_sectors",
            "internal_all_sectors",
            "internal_all_sectors_changed",
            "categories",
            "internal_categories",
            "internal_categories_changed",
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
            "light_touch_reviews",
            "internal_main_sector",
        )
        read_only_fields = (
            "id",
            "internal_code",
            "internal_id",
            "title_updated_on",
            "internal_title_changed",
            "internal_title_at_update",
            "summary_updated_on",
            "internal_summary_changed",
            "internal_summary_at_update",
            "status",
            "internal_status",
            "internal_status_changed",
            "status_date",
            "internal_status_date",
            "internal_status_date_changed",
            "is_resolved",
            "internal_is_resolved",
            "internal_is_resolved_changed",
            "country",
            "internal_country",
            "internal_country_changed",
            "trading_bloc",
            "internal_trading_bloc",
            "internal_trading_bloc_changed",
            "location",
            "internal_location",
            "internal_location_changed",
            "sectors",
            "internal_sectors",
            "internal_sectors_changed",
            "all_sectors",
            "internal_all_sectors",
            "internal_all_sectors_changed",
            "categories",
            "internal_categories",
            "internal_categories_changed",
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
            "internal_main_sector",
        )

    def get_internal_title_changed(self, obj):
        return obj.internal_title_changed

    def get_internal_summary_changed(self, obj):
        return obj.internal_summary_changed

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
    main_sector = SectorField(source="internal_main_sector")
    all_sectors = ReadOnlyAllSectorsField()
    categories = ReadOnlyCategoriesField()

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
            "categories",
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
    categories = ReadOnlyCategoriesField(to_repr_keys=("name",))
    reported_on = serializers.DateTimeField(source="internal_created_on")

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
            "categories",
            "last_published_on",
            "reported_on",
        )

    def get_sectors(self, obj):
        if obj.all_sectors:
            return [{"name": "All sectors"}]
        else:
            # we need to add the main sector into the list as the first field of the array
            sectors = [obj.internal_main_sector] + obj.sectors
            return ReadOnlySectorsField(
                to_repr_keys=("name",), sort=False
            ).to_representation(sectors)


def public_barriers_to_json(public_barriers=None):
    """
    Helper to serialize latest published version of published barriers.
    Public Barriers in the flat file should look similar.
    {
        "barriers": [
            {
                "id": "kjdfhkzx",
                "title": "Belgian chocolate...",
                "summary": "Lorem ipsum",
                "status": {"name": "Open",}
                "country": {"name": "Belgium",}
                "caused_by_trading_bloc": false,
                "trading_bloc": null,
                "location": "Belgium"
                "sectors: [
                    {"name": "Automotive"}
                ],
                "categories": [
                    {"name": "Goods and Services"}
                ],
                "last_published_on: "date",
                "reported_on": "date"
            }
        ]
    }
    If all sectors is true, use the sectors key to represent that as follows:
        "sectors: [{"name": "All sectors"}],
    """
    if public_barriers is None:
        public_barriers = (
            pb.latest_published_version for pb in get_published_public_barriers()
        )
    serializer = PublicPublishedVersionSerializer(public_barriers, many=True)
    return serializer.data
