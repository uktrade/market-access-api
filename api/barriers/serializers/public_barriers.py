from rest_framework import serializers

from api.barriers.fields import (
    NoneToBlankCharField,
    ReadOnlyStatusField,
    ReadOnlyCountryField,
    ReadOnlySectorsField,
    ReadOnlyAllSectorsField,
    ReadOnlyCategoriesField,
    TradingBlocField,
)
from api.barriers.models import PublicBarrier
from api.core.serializers.mixins import AllowNoneAtToRepresentationMixin


class NestedPublicBarrierSerializer(serializers.ModelSerializer):
    """
    Simple serializer for use within BarrierDetailSerializer.
    """
    class Meta:
        model = PublicBarrier
        fields = (
            "public_view_status",
        )


class PublicBarrierSerializer(AllowNoneAtToRepresentationMixin,
                              serializers.ModelSerializer):
    """
    Generic serializer for barrier public data.
    """
    title = NoneToBlankCharField()
    summary = NoneToBlankCharField()
    internal_title_changed = serializers.SerializerMethodField()
    internal_summary_changed = serializers.SerializerMethodField()
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

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "title",
            "title_updated_on",
            "internal_title_changed",
            "internal_title_at_update",
            "summary",
            "summary_updated_on",
            "internal_summary_changed",
            "internal_summary_at_update",
            "status",
            "internal_status",
            "internal_status_changed",
            "country",
            "internal_country",
            "internal_country_changed",
            "trading_bloc",
            "internal_trading_bloc",
            "internal_trading_bloc_changed",
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
        )
        read_only_fields = (
            "id",
            "title_updated_on",
            "internal_title_changed",
            "internal_title_at_update",
            "summary_updated_on",
            "internal_summary_changed",
            "internal_summary_at_update",
            "status",
            "internal_status",
            "internal_status_changed",
            "country",
            "internal_country",
            "internal_country_changed",
            "trading_bloc",
            "internal_trading_bloc",
            "internal_trading_bloc_changed",
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


class PublishedVersionSerializer(AllowNoneAtToRepresentationMixin,
                                 serializers.ModelSerializer):
    title = serializers.CharField()
    summary = serializers.CharField()
    status = ReadOnlyStatusField()
    country = ReadOnlyCountryField()
    sectors = ReadOnlySectorsField()
    all_sectors = ReadOnlyAllSectorsField()
    categories = ReadOnlyCategoriesField()

    class Meta:
        model = PublicBarrier
        fields = (
            "id",
            "title",
            "summary",
            "status",
            "country",
            "sectors",
            "all_sectors",
            "categories",
        )


# TODO: write a serializer that can be used to output the JSON blob onto S3
# As per contract (from slack chat with Michal)
# Public Barriers in the flat file should look as follows
# {
#     "barriers": [
#         {
#             "id": "1",
#             "title": "Belgian chocolate...",
#             "summary": "Lorem ipsum",
#             "status": "Open: in progress,
#             "country": "Belgium",
#             "sectors: [
#                 {"name": "Automotive"}
#             ],
#             "all_sectors": False,
#             "categories": [
#                 {"name": "Goods and Services"}
#             ]
#         }
#     ]
# }
