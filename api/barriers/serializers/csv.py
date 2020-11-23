from django.conf import settings

from rest_framework import serializers

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember

from api.metadata.constants import (
    BARRIER_SOURCE,
    BarrierStatus,
    BARRIER_PENDING,
    BARRIER_TERMS,
    PublicBarrierStatus,
    TRADE_DIRECTION_CHOICES,
)

from api.metadata.utils import (
    get_admin_area,
    get_country,
    get_sector,
    get_trading_bloc,
    get_trading_bloc_overseas_regions,
)


class BarrierCsvExportSerializer(serializers.Serializer):
    """ Serializer for CSV export """

    id = serializers.UUIDField()
    code = serializers.CharField()
    term = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_date = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    title = serializers.CharField()
    sectors = serializers.SerializerMethodField()
    overseas_region = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    admin_areas = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    product = serializers.CharField()
    source = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    team_count = serializers.IntegerField()
    reported_on = serializers.DateTimeField(format="%Y-%m-%d")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d")
    assessment_rating = serializers.SerializerMethodField()
    value_to_economy = serializers.SerializerMethodField()
    import_market_size = serializers.SerializerMethodField()
    commercial_value = serializers.IntegerField()
    export_value = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    trade_direction = serializers.SerializerMethodField()
    end_date = serializers.DateField(format="%Y-%m-%d")
    link = serializers.SerializerMethodField()
    economic_assessment_explanation = serializers.SerializerMethodField()
    wto_has_been_notified = serializers.SerializerMethodField()
    wto_should_be_notified = serializers.SerializerMethodField()
    wto_committee_notified = serializers.CharField(
        source="wto_profile.committee_notified.name",
        default="",
    )
    wto_committee_notification_link = serializers.CharField(
        source="wto_profile.committee_notification_link",
        default="",
    )
    wto_member_states = serializers.SerializerMethodField()
    wto_committee_raised_in = serializers.CharField(
        source="wto_profile.committee_raised_in.name",
        default="",
    )
    wto_raised_date = serializers.DateField(
        source="wto_profile.raised_date",
        default="",
        format="%Y-%m-%d",
    )
    wto_case_number = serializers.CharField(
        source="wto_profile.case_number",
        default="",
    )
    first_published_on = serializers.DateTimeField(
        source="public_barrier.first_published_on",
        format="%Y-%m-%d"
    )
    last_published_on = serializers.DateTimeField(
        source="public_barrier.last_published_on",
        format="%Y-%m-%d"
    )
    public_view_status = serializers.SerializerMethodField()
    changed_since_published = serializers.SerializerMethodField()
    commodity_codes = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()
    public_title = serializers.CharField(source="public_barrier.title")
    public_summary = serializers.CharField(source="public_barrier.summary")
    public_is_resolved = serializers.SerializerMethodField()
    latest_publish_note = serializers.SerializerMethodField()
    resolvability_assessment_time = serializers.SerializerMethodField()
    resolvability_assessment_effort = serializers.SerializerMethodField()
    strategic_assessment_scale = serializers.SerializerMethodField()

    class Meta:
        model = Barrier
        fields = (
            "id",
            "code",
            "title",
            "status",
            "status_date",
            "priority",
            "overseas_region",
            "country",
            "admin_areas",
            "sectors",
            "product",
            "source",
            "team_count",
            "term",
            "priority",
            "team_count",
            "reported_on",
            "modified_on",
            "assessment_rating",
            "value_to_economy",
            "import_market_size",
            "commercial_value",
            "export_value",
            "end_date",
            "link",
            "economic_assessment_explanation",
        )

    def get_term(self, obj):
        term_dict = dict(BARRIER_TERMS)
        return term_dict.get(obj.term, "Unknown")

    def get_assessment_rating(self, obj):
        if obj.current_economic_assessment:
            return obj.current_economic_assessment.get_rating_display()

    def get_value_to_economy(self, obj):
        if obj.current_economic_assessment:
            return obj.current_economic_assessment.value_to_economy

    def get_import_market_size(self, obj):
        if obj.current_economic_assessment:
            return obj.current_economic_assessment.import_market_size

    def get_export_value(self, obj):
        if obj.current_economic_assessment:
            return obj.current_economic_assessment.export_value

    def get_status(self, obj):
        """  Custom Serializer Method Field for exposing current status display value """
        status_dict = dict(BarrierStatus.choices)
        sub_status_dict = dict(BARRIER_PENDING)
        status = status_dict.get(obj.status, "Unknown")
        if status == "Open: Pending action":
            status = f"{status} ({sub_status_dict.get(obj.sub_status, 'Unknown')})"
        return status

    def get_status_date(self, obj):
        if obj.status_date:
            return obj.status_date.strftime("%Y-%m-%d")
        else:
            return None

    def get_summary(self, obj):
        if obj.is_summary_sensitive:
            return "OFFICIAL-SENSITIVE (see it on DMAS)"
        else:
            return obj.summary or None

    def get_sectors(self, obj):
        if obj.sectors_affected:
            if obj.all_sectors:
                return "All"
            else:
                sector_names = []
                for sector_id in obj.sectors:
                    sector = get_sector(str(sector_id))
                    if sector and sector.get("name"):
                        sector_names.append(sector.get("name"))
                return sector_names
        else:
            return "N/A"

    def get_location(self, obj):
        if obj.country:
            country = get_country(str(obj.country))
            if country:
                return country.get("name")
        elif obj.trading_bloc:
            trading_bloc = get_trading_bloc(obj.trading_bloc)
            if trading_bloc:
                return trading_bloc.get("name")

    def get_overseas_region(self, obj):
        if obj.country:
            country = get_country(str(obj.country))
            if country:
                overseas_region = country.get("overseas_region")
                if overseas_region:
                    return overseas_region.get("name")
        elif obj.trading_bloc:
            overseas_regions = get_trading_bloc_overseas_regions(obj.trading_bloc)
            return [region["name"] for region in overseas_regions]

    def get_admin_areas(self, obj):
        admin_area_names = []
        for admin_area in obj.admin_areas or []:
            admin_area = get_admin_area(str(admin_area))
            if admin_area and admin_area.get("name"):
                admin_area_names.append(admin_area.get("name"))
        return admin_area_names

    def get_categories(self, obj):
        return [category.title for category in obj.categories.all()]

    def get_source(self, obj):
        """  Custom Serializer Method Field for exposing source display value """
        source_dict = dict(BARRIER_SOURCE)
        return source_dict.get(obj.source, "Unknown")

    def get_priority(self, obj):
        """  Custom Serializer Method Field for exposing barrier priority """
        if obj.priority:
            return obj.priority.name
        else:
            return "Unknown"

    def get_team_count(self, obj):
        if hasattr(obj, "team_count"):
            return obj.team_count
        return TeamMember.objects.filter(barrier=obj).count()

    def get_tags(self, obj):
        return [tag.title for tag in obj.tags.all()]

    def get_trade_direction(self, obj):
        if obj.trade_direction:
            trade_directions = dict((str(x), y) for x, y in TRADE_DIRECTION_CHOICES)
            return trade_directions.get(str(obj.trade_direction))
        else:
            return None

    def get_link(self, obj):
        return f"{settings.DMAS_BASE_URL}/barriers/{obj.code}"

    def get_economic_assessment_explanation(self, obj):
        if obj.current_economic_assessment:
            return obj.current_economic_assessment.explanation

    def get_wto_has_been_notified(self, obj):
        if obj.has_wto_profile:
            if obj.wto_profile.wto_has_been_notified is True:
                return "Yes"
            elif obj.wto_profile.wto_has_been_notified is False:
                return "No"

    def get_wto_should_be_notified(self, obj):
        if obj.has_wto_profile:
            if obj.wto_profile.wto_should_be_notified is True:
                return "Yes"
            elif obj.wto_profile.wto_should_be_notified is False:
                return "No"

    def get_wto_member_states(self, obj):
        if obj.has_wto_profile:
            return [
                get_country(str(country_id)).get("name")
                for country_id in obj.wto_profile.member_states
            ]

    def get_commodity_codes(self, obj):
        return [
            barrier_commodity.simple_formatted_code
            for barrier_commodity in obj.barrier_commodities.all()
        ]

    def get_public_id(self, obj):
        if obj.has_public_barrier and obj.public_barrier.is_currently_published:
            return f"PID-{obj.public_barrier.pk}"

    def get_public_view_status(self, obj):
        if obj.has_public_barrier:
            return obj.public_barrier.get__public_view_status_display()
        return PublicBarrierStatus.choices[PublicBarrierStatus.UNKNOWN]

    def get_changed_since_published(self, obj):
        if obj.has_public_barrier and obj.public_barrier.is_currently_published:
            relevant_changes = (
                "barrier.categories",
                "barrier.location",
                "barrier.sectors",
                "barrier.status",
                "barrier.summary",
                "barrier.title",
            )
            for history_item in obj.cached_history_items.all():
                if history_item.date > obj.public_barrier.last_published_on:
                    change = f"{history_item.model}.{history_item.field}"
                    if change in relevant_changes:
                        return "Yes"
            return "No"

    def get_public_is_resolved(self, obj):
        if obj.has_public_barrier and obj.public_barrier.is_currently_published:
            if obj.public_barrier.is_resolved:
                return "Yes"
            return "No"

    def get_latest_publish_note(self, obj):
        if obj.has_public_barrier:
            notes = [note for note in obj.public_barrier.notes.all()]
            if notes:
                notes.sort(key=lambda note: note.created_on, reverse=True)
                return notes[0].text

    def get_resolvability_assessment_time(self, obj):
        if obj.current_resolvability_assessment:
            return obj.current_resolvability_assessment.time_to_resolve

    def get_resolvability_assessment_effort(self, obj):
        if obj.current_resolvability_assessment:
            return obj.current_resolvability_assessment.effort_to_resolve

    def get_strategic_assessment_scale(self, obj):
        if obj.current_strategic_assessment:
            return obj.current_strategic_assessment.scale
