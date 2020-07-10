from django.core.cache import cache
from rest_framework import serializers

from api.barriers.models import BarrierInstance
from api.collaboration.models import TeamMember
from api.metadata.constants import (
    ASSESMENT_IMPACT,
    BARRIER_PENDING,
    BARRIER_SOURCE,
    BARRIER_STATUS,
    PROBLEM_STATUS_TYPES,
)
from api.metadata.utils import (
    get_admin_areas,
    get_countries,
    get_sectors,
)


class BarrierDataSetSerializer(serializers.Serializer):
    """
    Serializer for Data Workspace View
    """

    id = serializers.UUIDField()
    code = serializers.CharField()
    scope = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    barrier_title = serializers.CharField()
    sectors = serializers.SerializerMethodField()
    overseas_region = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    admin_areas = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    product = serializers.CharField()
    source = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    status_date = serializers.DateField(format="%Y-%m-%d")
    reported_on = serializers.DateTimeField(format="%Y-%m-%d")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d")
    assessment_impact = serializers.SerializerMethodField()
    value_to_economy = serializers.SerializerMethodField()
    import_market_size = serializers.SerializerMethodField()
    commercial_value = serializers.SerializerMethodField()
    commercial_value_explanation = serializers.SerializerMethodField()
    export_value = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    company_names = serializers.SerializerMethodField()
    company_ids = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "barrier_title",
            "status",
            "priority",
            "overseas_region",
            "country",
            "admin_areas",
            "sectors",
            "product",
            "scope",
            "categories",
            "source",
            "team_count",
            "status_date",
            "reported_on",
            "modified_on",
            "assessment_impact",
            "value_to_economy",
            "import_market_size",
            "commercial_value",
            "commercial_value_explanation",
            "export_value",
        )

    def get_scope(self, obj):
        """
        Custom Serializer Method Field for exposing current problem scope display value
        """
        problem_status_dict = dict(PROBLEM_STATUS_TYPES)
        return problem_status_dict.get(obj.problem_status, "Unknown")

    def get_assessment_impact(self, obj):
        if hasattr(obj, "assessment"):
            impact_dict = dict(ASSESMENT_IMPACT)
            return impact_dict.get(obj.assessment.impact, None)
        return None

    def get_value_to_economy(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.value_to_economy
        return None

    def get_import_market_size(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.import_market_size
        return None

    def get_commercial_value(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.commercial_value
        return None

    def get_commercial_value_explanation(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.commercial_value_explanation
        return None

    def get_export_value(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.export_value
        return None

    def get_status(self, obj):
        """  Custom Serializer Method Field for exposing current status display value """
        status_dict = dict(BARRIER_STATUS)
        sub_status_dict = dict(BARRIER_PENDING)
        status = status_dict.get(obj.status, "Unknown")
        if status == "Open: Pending action":
            status = f"{status} ({sub_status_dict.get(obj.sub_status, 'Unknown')})"
        return status

    def get_sectors(self, obj):
        if obj.sectors_affected:
            if obj.all_sectors:
                return "All"
            else:
                dh_sectors = cache.get_or_set("dh_sectors", get_sectors, 72000)
                sectors = []
                if obj.sectors:
                    for sector in obj.sectors:
                        sectors.extend([s["name"] for s in dh_sectors if s["id"] == str(sector)])
                return sectors
        else:
            return "N/A"

    def get_country(self, obj):
        dh_countries = cache.get_or_set("dh_countries", get_countries, 72000)
        country = [c["name"] for c in dh_countries if c["id"] == str(obj.export_country)]
        return country

    def get_overseas_region(self, obj):
        dh_countries = cache.get_or_set("dh_countries", get_countries, 72000)
        country = [c for c in dh_countries if c["id"] == str(obj.export_country)]
        if len(country) > 0:
            overseas_region = country[0].get("overseas_region", None)
            if overseas_region is not None:
                return overseas_region["name"]
        return None

    def get_admin_areas(self, obj):
        dh_areas = cache.get_or_set("dh_admin_areas", get_admin_areas, 72000)
        areas = []
        if obj.country_admin_areas:
            for area in obj.country_admin_areas:
                areas.extend([a["name"] for a in dh_areas if a["id"] == str(area)])
        return areas

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
        return TeamMember.objects.filter(barrier=obj).count()

    def get_company_names(self, obj):
        """
        Unpack companies json field into company names
        """
        if obj.companies:
            return [company['name'] for company in obj.companies if company.get('name')]

    def get_company_ids(self, obj):
        """
        Unpack companies json field into company ids
        """
        if obj.companies:
            return [company['id'] for company in obj.companies if company.get('id')]
