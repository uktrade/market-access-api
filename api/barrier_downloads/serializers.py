import logging

from django.conf import settings
from rest_framework import serializers

from api.metadata.constants import (
    BARRIER_PENDING,
    GOVERNMENT_ORGANISATION_TYPES,
    TOP_PRIORITY_BARRIER_STATUS,
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


class BarrierDownloadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    created_by = serializers.CharField()
    created_on = serializers.DateTimeField()
    modified_on = serializers.DateTimeField()
    filters = serializers.JSONField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class BarrierDownloadPatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256, required=True)


class BarrierDownloadPresignedUrlSerializer(serializers.Serializer):
    presigned_url = serializers.CharField()


class CsvDownloadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    title = serializers.CharField()
    summary = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    priority_level = serializers.CharField()
    overseas_region = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    admin_areas = serializers.SerializerMethodField()
    sectors = serializers.SerializerMethodField()
    product = serializers.CharField()
    reported_by = serializers.SerializerMethodField()
    reported_on = serializers.DateTimeField(format="%Y-%m-%d")
    barrier_owner = serializers.SerializerMethodField()
    status_date = serializers.SerializerMethodField()
    resolved_date = serializers.SerializerMethodField()
    status_summary = serializers.SerializerMethodField()
    modified_on = serializers.DateTimeField(format="%Y-%m-%d", allow_null=True)
    tags = serializers.SerializerMethodField()
    trade_direction = serializers.CharField(source="get_trade_direction_display")
    is_top_priority = serializers.SerializerMethodField()
    is_resolved_top_priority = serializers.SerializerMethodField()
    government_organisations = serializers.SerializerMethodField()
    progress_update_status = serializers.SerializerMethodField()
    progress_update_message = serializers.SerializerMethodField()
    progress_update_next_steps = serializers.SerializerMethodField()
    next_steps_items = serializers.SerializerMethodField()
    programme_fund_progress_update_milestones = serializers.SerializerMethodField()
    programme_fund_progress_update_expenditure = serializers.SerializerMethodField()
    programme_fund_progress_update_date = serializers.SerializerMethodField()
    programme_fund_progress_update_author = serializers.SerializerMethodField()
    estimated_resolution_date = serializers.DateField(format="%b-%y")
    proposed_estimated_resolution_date = serializers.SerializerMethodField()
    commodity_codes = serializers.SerializerMethodField()
    public_view_status = serializers.SerializerMethodField()
    changed_since_published = serializers.SerializerMethodField()
    public_title = serializers.CharField(source="public_barrier.title")
    public_summary = serializers.CharField(source="public_barrier.summary")
    economic_assessment_rating = serializers.SerializerMethodField()
    value_to_economy = serializers.SerializerMethodField()
    valuation_assessment_rating = serializers.SerializerMethodField()
    valuation_assessment_midpoint = serializers.SerializerMethodField()
    valuation_assessment_explanation = serializers.SerializerMethodField()
    commercial_value = serializers.IntegerField()
    policy_teams = serializers.SerializerMethodField()

    def get_policy_teams(self, obj):
        return [p.title for p in obj.policy_teams.all()]

    def get_is_top_priority(self, obj):
        return obj.is_top_priority

    def get_is_resolved_top_priority(self, obj):
        return obj.top_priority_status == TOP_PRIORITY_BARRIER_STATUS.RESOLVED

    def get_link(self, obj):
        return f"{settings.DMAS_BASE_URL}/barriers/{obj.code}"

    def get_location(self, barrier):
        if barrier.country:
            country = get_country(str(barrier.country))
            if country:
                return country.get("name")
        elif barrier.trading_bloc:
            trading_bloc = get_trading_bloc(barrier.trading_bloc)
            if trading_bloc:
                return trading_bloc.get("name")

    def get_overseas_region(self, barrier):
        if barrier.country:
            country = get_country(str(barrier.country))
            if country:
                overseas_region = country.get("overseas_region")
                if overseas_region:
                    return overseas_region.get("name")
        elif barrier.trading_bloc:
            overseas_regions = get_trading_bloc_overseas_regions(barrier.trading_bloc)
            return [region["name"] for region in overseas_regions]

    def get_admin_areas(self, barrier):
        admin_area_names = []
        for admin_area in barrier.admin_areas:
            admin_area = get_admin_area(str(admin_area))
            if admin_area and admin_area.get("name"):
                admin_area_names.append(admin_area.get("name"))
        return admin_area_names

    def get_sectors(self, barrier):
        if barrier.sectors_affected:
            if barrier.all_sectors:
                return "All"
            else:
                sector_names = []
                for sector_id in barrier.sectors:
                    sector = get_sector(str(sector_id))
                    if sector and sector.get("name"):
                        sector_names.append(sector.get("name"))
                return sector_names
        else:
            return "N/A"

    def get_summary(self, barrier):
        return (
            barrier.summary
            if not barrier.is_summary_sensitive
            else "OFFICIAL-SENSITIVE (see it on DMAS)"
        )

    def get_status_summary(self, barrier):
        return (
            barrier.status_summary
            if not barrier.is_summary_sensitive
            else "OFFICIAL-SENSITIVE (see it on DMAS)"
        )

    def get_status(self, barrier):
        """Custom Serializer Method Field for exposing current status display value"""
        status_dict = dict(BarrierStatus.choices)
        sub_status_dict = dict(BARRIER_PENDING)
        status = status_dict.get(barrier.status, "Unknown")
        if status == "Open: Pending action":
            status = f"{status} ({sub_status_dict.get(barrier.sub_status, 'Unknown')})"
        return status

    def get_reported_by(self, barrier):
        reported_by = None
        if barrier.created_by:
            first_name = barrier.created_by.first_name
            last_name = barrier.created_by.last_name
            reported_by = (
                f"{first_name} {last_name}" if first_name and last_name else None
            )
        return reported_by

    def get_barrier_owner(self, barrier):
        barrier_team = barrier.barrier_team.all()

        if not barrier_team:
            return

        owner = barrier_team[0].user

        if not owner:
            return

        first_name = owner.first_name
        last_name = owner.last_name
        return f"{first_name} {last_name}" if first_name and last_name else None

    def get_tags(self, barrier):
        return [tag.title for tag in barrier.tags.all()]

    def get_government_organisations(self, obj):
        return [
            org.name
            for org in obj.organisations.all()
            if org.organisation_type in GOVERNMENT_ORGANISATION_TYPES
        ]

    def get_progress_update_status(self, barrier):
        latest_progress_updates = barrier.progress_updates.all()
        if latest_progress_updates.exists():
            return latest_progress_updates.first().get_status_display()
        return None

    def get_progress_update_message(self, barrier):
        latest_progress_updates = barrier.progress_updates.all()
        if latest_progress_updates.exists():
            return latest_progress_updates.first().update
        return None

    def get_progress_update_next_steps(self, barrier):
        latest_progress_updates = barrier.progress_updates.all()
        if latest_progress_updates.exists():
            return latest_progress_updates.first().next_steps

    def get_next_steps_items(self, barrier):
        item_summary = []
        for item in barrier.next_steps_items.all():
            # Add item to list if still pending
            item_summary.append(
                f"{item.completion_date.strftime('%b %Y')}: {item.next_step_owner}, {item.next_step_item}"
            )
        if not item_summary:
            return

        return "\u2022\u00A0" + "\n\u2022\u00A0".join(item_summary)

    def get_resolved_date(self, barrier):
        if barrier.status_date and (barrier.status == 4 or barrier.status == 3):
            return barrier.status_date.strftime("%d-%b-%y")

    def get_status_date(self, barrier):
        if barrier.status_date:
            return barrier.status_date.strftime("%Y-%m-%d")

    def get_programme_fund_progress_update_milestones(self, barrier):
        qs = barrier.programme_fund_progress_updates.all()
        if qs.exists():
            return qs.first().milestones_and_deliverables

    def get_programme_fund_progress_update_expenditure(self, barrier):
        qs = barrier.programme_fund_progress_updates.all()
        if qs.exists():
            return qs.first().expenditure

    def get_programme_fund_progress_update_date(self, barrier):
        qs = barrier.programme_fund_progress_updates.all()
        if qs.exists():
            return qs.first().created_on

    def get_programme_fund_progress_update_author(self, barrier):
        qs = barrier.programme_fund_progress_updates.all()
        if qs.exists():
            author = qs.first().created_by
            first_name = getattr(author, "first_name", None)
            last_name = getattr(author, "last_name", None)
            return f"{first_name} {last_name}" if first_name and last_name else None

    def get_proposed_estimated_resolution_date(self, barrier):
        # only show the proposed date if it is different to the current date
        if not barrier.proposed_estimated_resolution_date:
            return None

        # compare to estimated_resolution_date
        if (
            barrier.proposed_estimated_resolution_date
            == barrier.estimated_resolution_date
        ):
            return None

        return barrier.proposed_estimated_resolution_date.strftime("%b-%y")

    def get_commodity_codes(self, barrier):
        return (
            "; ".join(
                [
                    str(barrier_commodity.simple_formatted_code)
                    for barrier_commodity in barrier.barrier_commodities.all()
                ]
            )
            + ";"
        )

    def get_public_view_status(self, barrier):
        if barrier.has_public_barrier:
            return barrier.public_barrier.get__public_view_status_display()
        return PublicBarrierStatus.choices[PublicBarrierStatus.UNKNOWN]

    def get_changed_since_published(self, barrier):
        if (
            barrier.has_public_barrier
            and barrier.public_barrier.status == PublicBarrierStatus.PUBLISHED
        ):
            if barrier.public_barrier.changed_since_published:
                return "Yes"
            return "No"

    def get_economic_assessment_rating(self, barrier):
        assessment = barrier.current_economic_assessment
        if assessment:
            return assessment.get_rating_display()

    def get_value_to_economy(self, barrier):
        assessment = barrier.current_economic_assessment
        if assessment:
            return assessment.export_potential.get("uk_exports_affected")

    def get_valuation_assessment_midpoint(self, barrier):
        latest_valuation_assessment = barrier.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.midpoint

    def get_valuation_assessment_rating(self, barrier):
        latest_valuation_assessment = barrier.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.rating

    def get_valuation_assessment_explanation(self, barrier):
        latest_valuation_assessment = barrier.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.explanation
