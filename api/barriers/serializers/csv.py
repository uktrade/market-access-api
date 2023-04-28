import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.barriers.models import (
    Barrier,
    BarrierRequestDownloadApproval,
    BarrierTopPrioritySummary,
)
from api.barriers.serializers.mixins import AssessmentFieldsMixin
from api.collaboration.models import TeamMember
from api.history.factories.public_barriers import PublicBarrierHistoryFactory
from api.metadata.constants import (
    BARRIER_PENDING,
    BARRIER_SOURCE,
    BARRIER_TERMS,
    GOVERNMENT_ORGANISATION_TYPES,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_DIRECTION_CHOICES,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.metadata.utils import (
    get_admin_area,
    get_country,
    get_sector,
    get_trading_bloc,
    get_trading_bloc_overseas_regions,
)

logger = logging.getLogger(__name__)


class BarrierCsvExportSerializer(AssessmentFieldsMixin, serializers.Serializer):
    """Serializer for CSV export"""

    id = serializers.UUIDField()
    code = serializers.CharField()
    term = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_date = serializers.SerializerMethodField()
    resolved_date = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    status_summary = serializers.SerializerMethodField()
    title = serializers.CharField()
    sectors = serializers.SerializerMethodField()
    overseas_region = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    admin_areas = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    product = serializers.CharField()
    source = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    priority_level = serializers.CharField()
    reported_on = serializers.DateTimeField(format="%Y-%m-%d")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d")
    commercial_value = serializers.IntegerField()
    team_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    trade_direction = serializers.SerializerMethodField()
    estimated_resolution_date = serializers.DateField(format="%b-%y")
    proposed_estimated_resolution_date = serializers.SerializerMethodField()
    previous_estimated_resolution_date = serializers.SerializerMethodField()
    estimated_resolution_updated_date = serializers.SerializerMethodField()
    estimated_resolution_date_change_reason = serializers.CharField()
    link = serializers.SerializerMethodField()
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
        source="public_barrier.first_published_on", format="%Y-%m-%d"
    )
    last_published_on = serializers.DateTimeField(
        source="public_barrier.last_published_on", format="%Y-%m-%d"
    )
    public_view_status = serializers.SerializerMethodField()
    last_public_view_status_update = serializers.SerializerMethodField()
    public_eligibility_summary = serializers.CharField()
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
    government_organisations = serializers.SerializerMethodField()
    is_top_priority = serializers.BooleanField()
    top_priority_status = serializers.CharField()
    top_priority_summary = serializers.SerializerMethodField()
    is_resolved_top_priority = serializers.SerializerMethodField()

    # progress update fields
    progress_update_status = serializers.SerializerMethodField()
    progress_update_message = serializers.SerializerMethodField()
    progress_update_date = serializers.SerializerMethodField()
    progress_update_author = serializers.SerializerMethodField()
    progress_update_next_steps = serializers.SerializerMethodField()
    next_steps_items = serializers.SerializerMethodField()
    programme_fund_progress_update_milestones = serializers.SerializerMethodField()
    programme_fund_progress_update_expenditure = serializers.SerializerMethodField()
    programme_fund_progress_update_date = serializers.SerializerMethodField()
    programme_fund_progress_update_author = serializers.SerializerMethodField()

    # regional trade plan fields
    is_regional_trade_plan = serializers.SerializerMethodField()

    class Meta:
        model = Barrier
        fields = (
            "id",
            "code",
            "title",
            "status",
            "status_summary",
            "status_date",
            "priority",
            "priority_level",
            "overseas_region",
            "country",
            "admin_areas",
            "sectors",
            "product",
            "source",
            "team_count",
            "term",
            "reported_on",
            "modified_on",
            "economic_assessment_rating",
            "economic_assessment_explanation",
            "value_to_economy",
            "import_market_size",
            "valuation_assessment_rating",
            "valuation_assessment_midpoint",
            "valuation_assessment_midpoint_value",
            "valuation_assessment_explanation",
            "commercial_value",
            "estimated_resolution_date",
            "proposed_estimated_resolution_date",
            "previous_estimated_resolution_date",
            "estimated_resolution_updated_date",
            "estimated_resolution_date_change_reason",
            "link",
            "progress_update_status",
            "progress_update_message",
            "progress_update_date",
            "progress_update_author",
            "progress_update_next_steps",
            "next_steps_items",
            "programme_fund_progress_update_milestones",
            "programme_fund_progress_update_expenditure",
            "programme_fund_progress_update_date",
            "programme_fund_progress_update_author",
            "is_top_priority",
            "top_priority_status",
            "is_resolved_top_priority",
            "top_priority_summary",
            "government_organisations",
            "is_regional_trade_plan",
        )

    def get_term(self, obj):
        term_dict = dict(BARRIER_TERMS)
        return term_dict.get(obj.term, "Unknown")

    def get_status(self, obj):
        """Custom Serializer Method Field for exposing current status display value"""
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

    def get_resolved_date(self, obj):
        if obj.status_date and (obj.status == 4 or obj.status == 3):
            return obj.status_date.strftime("%d-%b-%y")
        else:
            return None

    def get_summary(self, obj):
        if obj.is_summary_sensitive:
            return "OFFICIAL-SENSITIVE (see it on DMAS)"
        else:
            return obj.summary or None

    def get_status_summary(self, obj):
        if obj.is_summary_sensitive:
            return "OFFICIAL-SENSITIVE (see it on DMAS)"
        else:
            return obj.status_summary or None

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
        """Custom Serializer Method Field for exposing source display value"""
        source_dict = dict(BARRIER_SOURCE)
        return source_dict.get(obj.source, "Unknown")

    def get_priority(self, obj):
        """Custom Serializer Method Field for exposing barrier priority"""
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
        return (
            "; ".join(
                [
                    str(barrier_commodity.simple_formatted_code)
                    for barrier_commodity in obj.barrier_commodities.all()
                ]
            )
            + ";"
        )

    def get_public_id(self, obj):
        if obj.has_public_barrier and obj.public_barrier.is_currently_published:
            return f"PID-{obj.public_barrier.id.hashid}"

    def get_public_view_status(self, obj):
        if obj.has_public_barrier:
            return obj.public_barrier.get__public_view_status_display()
        return PublicBarrierStatus.choices[PublicBarrierStatus.UNKNOWN]

    def get_last_public_view_status_update(self, obj):
        history_items = PublicBarrierHistoryFactory.get_history_items(barrier_id=obj.id)
        changes_that_include_publice_view_status = filter(
            lambda history_item: history_item.data["field"] == "public_view_status",
            history_items,
        )
        change_dates = {
            change.data["date"] for change in changes_that_include_publice_view_status
        }
        try:
            return max(change_dates)
        except ValueError:
            # Empty sequence
            return None

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

    def get_government_organisations(self, obj):
        return [
            org.name
            for org in obj.organisations.all()
            if org.organisation_type in GOVERNMENT_ORGANISATION_TYPES
        ]

    def get_progress_update_status(self, obj):
        if obj.latest_progress_update:
            return obj.latest_progress_update.get_status_display()
        return None

    def get_progress_update_message(self, obj):
        if obj.latest_progress_update:
            return obj.latest_progress_update.update

    def get_progress_update_date(self, obj):
        if obj.latest_progress_update:
            return obj.latest_progress_update.created_on
        return None

    def get_progress_update_author(self, obj):
        if obj.latest_progress_update:
            return (
                f"{obj.latest_progress_update.created_by.first_name} "
                + obj.latest_progress_update.created_by.last_name
            )

        return None

    def get_progress_update_next_steps(self, obj):
        if obj.latest_progress_update:
            return obj.latest_progress_update.next_steps
        return None

    def get_next_steps_items(self, obj):
        item_summary_paragraph = None
        if obj.next_steps_items:
            item_summary = []
            for item in obj.next_steps_items.filter(status="IN_PROGRESS").order_by(
                "completion_date"
            ):
                # Add item to list if still pending
                item_summary.append(
                    f"{item.completion_date.strftime('%b %Y')}: {item.next_step_owner}, {item.next_step_item}"
                )
            item_summary_paragraph = "\u2022\u00A0" + "\n\u2022\u00A0".join(
                item_summary
            )
        return item_summary_paragraph

    def get_programme_fund_progress_update_milestones(self, obj):
        if obj.latest_programme_fund_progress_update:
            return obj.latest_programme_fund_progress_update.milestones_and_deliverables
        return None

    def get_programme_fund_progress_update_expenditure(self, obj):
        if obj.latest_programme_fund_progress_update:
            return obj.latest_programme_fund_progress_update.expenditure

    def get_programme_fund_progress_update_date(self, obj):
        if obj.latest_programme_fund_progress_update:
            return obj.latest_programme_fund_progress_update.created_on
        return None

    def get_programme_fund_progress_update_author(self, obj):
        if obj.latest_programme_fund_progress_update:
            return (
                f"{obj.latest_programme_fund_progress_update.created_by.first_name} "
                + obj.latest_programme_fund_progress_update.created_by.last_name
            )

        return None

    def get_proposed_estimated_resolution_date(self, obj):
        # only show the proposed date if it is different to the current date
        if not obj.proposed_estimated_resolution_date:
            return None

        # compare to estimated_resolution_date
        if obj.proposed_estimated_resolution_date == obj.estimated_resolution_date:
            return None

        return obj.proposed_estimated_resolution_date.strftime("%b-%y")

    def get_previous_estimated_resolution_date(self, obj):
        try:
            history = (
                Barrier.history.filter(id=obj.id)
                .exclude(estimated_resolution_date=obj.estimated_resolution_date)
                .latest("history_date")
            )
        except ObjectDoesNotExist:
            # Error case if barriers are missing history
            return None

        if history.estimated_resolution_date:
            return history.estimated_resolution_date.strftime("%b-%y")
        else:
            return None

    def get_estimated_resolution_updated_date(self, obj):
        try:
            history = (
                Barrier.history.filter(id=obj.id)
                .exclude(estimated_resolution_date=obj.estimated_resolution_date)
                .latest("history_date")
            )
        except ObjectDoesNotExist:
            # Error case if barriers are missing history
            return None

        if history.estimated_resolution_date:
            return history.history_date.strftime("%Y-%m-%d")
        else:
            return None

    def get_is_regional_trade_plan(self, obj):
        return obj.is_regional_trade_plan

    def get_is_resolved_top_priority(self, obj):
        return obj.top_priority_status == TOP_PRIORITY_BARRIER_STATUS.RESOLVED

    def get_top_priority_summary(self, obj):
        priority_summary = BarrierTopPrioritySummary.objects.filter(barrier=obj.id)
        if priority_summary:
            latest_summary = priority_summary.latest("modified_on")
            return latest_summary.top_priority_summary_text
        else:
            return None


class BarrierRequestDownloadApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierRequestDownloadApproval
        fields = ("id", "user")
